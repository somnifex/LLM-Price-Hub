export type TModelPrice = {
  mode: "existing" | "new";
  standard_model_id: number | null;
  new_model_name: string;
  new_model_vendor: string;
  provider_model_name: string;
  price_in: number;
  price_out: number;
  cache_hit_input_price: number | null;
  cache_hit_output_price: number | null;
  currency: string;
  proof_type: "text" | "url";
  proof_content: string;
};
