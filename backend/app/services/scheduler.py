from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import Session, select
from app.database import engine
from app.models import CurrencyRate, ModelPrice, PriceStatus, Provider, SystemSetting
import httpx
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("scheduler")

scheduler = AsyncIOScheduler()

def get_db_session():
    return Session(engine)

def update_exchange_rates():
    """Fetch rates from public API and update DB."""
    try:
        # Default settings
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        api_key = ""
        
        with get_db_session() as session:
            settings = session.exec(select(SystemSetting)).all()
            settings_dict = {s.key: s.value for s in settings}
            
            curr_url = settings_dict.get("exchange_rate_url")
            if curr_url:
                url = curr_url
            
            curr_key = settings_dict.get("exchange_rate_key")
            if curr_key:
                api_key = curr_key
        
        # If user put placeholders or simple URL, handle it.
        # If API key exists, usually it's injected into URL or Header.
        # For simplicity, if key exists and URL contains {KEY}, replace it, otherwise append?
        # Let's assume the user provides the FULL URL or standard template.
        # If using exchangerate-api.com v6: https://v6.exchangerate-api.com/v6/YOUR-API-KEY/latest/USD
        
        if "{KEY}" in url and api_key:
            url = url.replace("{KEY}", api_key)
            
        with httpx.Client() as client:
            resp = client.get(url)
            if resp.status_code != 200:
                logger.error(f"Exchange rate API returned {resp.status_code}")
                return
                
            data = resp.json()
            # Support standard format (rates or conversion_rates)
            rates = data.get("rates") or data.get("conversion_rates") or {}
            base = data.get("base") or data.get("base_code") or "USD"
            
            # Normalize to USD if base is not USD
            usd_rate = rates.get("USD")
            if base != "USD" and usd_rate:
                new_rates = {}
                for k, v in rates.items():
                    if v is not None:
                        new_rates[k] = v / usd_rate
                rates = new_rates
                rates["USD"] = 1.0
            
        with get_db_session() as session:
            for code, rate in rates.items():
                if len(code) > 10: continue
                
                # Upsert logic
                existing = session.get(CurrencyRate, code)
                if existing:
                    existing.rate_to_usd = rate
                    existing.updated_at = datetime.utcnow()
                    session.add(existing)
                else:
                    new_rate = CurrencyRate(code=code, rate_to_usd=rate)
                    session.add(new_rate)
            session.commit()
        logger.info("Updated exchange rates")
    except Exception as e:
        logger.error(f"Failed to update rates: {e}")

def reschedule_exchange_job():
    """Reads interval from DB and reschedules the job."""
    try:
        interval = 240 # Default 4 hours (in minutes)
        with get_db_session() as session:
            s = session.get(SystemSetting, "exchange_rate_interval_minutes")
            if s and s.value.isdigit():
                interval = int(s.value)
        
        # Ensure minimum interval to avoid spam
        if interval < 5: interval = 5
        
        try:
            scheduler.reschedule_job('exchange_rates', trigger='interval', minutes=interval)
            logger.info(f"Rescheduled exchange rate job to every {interval} minutes")
        except:
            scheduler.add_job(update_exchange_rates, 'interval', minutes=interval, id='exchange_rates')
            logger.info(f"Added exchange rate job every {interval} minutes")
            
    except Exception as e:
        logger.error(f"Failed to reschedule job: {e}")

def expire_old_prices():
    """Expire prices verified more than 7 days ago."""
    try:
        with get_db_session() as session:
            # Logic: active and verified_at < 7 days ago
            cutoff = datetime.utcnow() - timedelta(days=7)
            statement = select(ModelPrice).where(
                ModelPrice.status == PriceStatus.active,
                ModelPrice.verified_at < cutoff
            )
            results = session.exec(statement).all()
            for price in results:
                price.status = PriceStatus.expired
                session.add(price)
            session.commit()
            logger.info(f"Expired {len(results)} prices")
    except Exception as e:
        logger.error(f"Failed to expire prices: {e}")

def check_one_provider(provider_id: int, url: str):
    """Check a single provider and update stats. (To be run potentially in parallel or sequential)"""
    # Simple check
    success = False
    try:
        if not url.startswith("http"):
            url = f"https://{url}"
        
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url)
            if resp.status_code < 400:
                success = True
    except:
        success = False
        
    with get_db_session() as session:
        provider = session.get(Provider, provider_id)
        if provider:
            # Moving average calculation
            current_val = 100.0 if success else 0.0
            # Alpha = 0.1 for smoothing
            provider.uptime_rate = (provider.uptime_rate * 0.9) + (current_val * 0.1)
            session.add(provider)
            session.commit()

def check_uptime():
    """Iterate all providers and check uptime."""
    try:
        with get_db_session() as session:
            providers = session.exec(select(Provider)).all()
            for p in providers:
                if p.website:
                    check_one_provider(p.id, p.website)
        logger.info("Checked provider uptime")
    except Exception as e:
        logger.error(f"Failed provider uptime check: {e}")

# Schedule Jobs
scheduler.add_job(update_exchange_rates, 'interval', hours=4, id='exchange_rates')
scheduler.add_job(expire_old_prices, 'cron', hour=0) # Daily
scheduler.add_job(check_uptime, 'interval', minutes=30)
