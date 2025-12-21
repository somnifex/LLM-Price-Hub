import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import Home from "@/views/Home.vue";
import Submit from "@/views/Submit.vue";
import Admin from "@/views/Admin.vue";
import Login from "@/views/Login.vue";
import Register from "@/views/Register.vue";
import AdminUsers from "@/views/AdminUsers.vue";
import AdminSettings from "@/views/AdminSettings.vue";
import AdminContent from "@/views/AdminContent.vue";
import UserSettings from "@/views/UserSettings.vue";
import VerifyEmail from "@/views/VerifyEmail.vue";

import SubmitAlpha from "@/views/SubmitAlpha.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "Home", component: Home },
    { path: "/login", name: "Login", component: Login },
    { path: "/register", name: "Register", component: Register },
    { path: "/verify-email", name: "VerifyEmail", component: VerifyEmail },
    {
      path: "/submit",
      name: "Submit",
      component: SubmitAlpha,
      meta: { requiresAuth: true },
    },
    {
      path: "/settings",
      name: "UserSettings",
      component: UserSettings,
      meta: { requiresAuth: true },
    },
    {
      path: "/admin",
      name: "Admin",
      component: Admin,
      meta: { requiresAuth: true, requiresAdmin: true },
      children: [
        { path: "", redirect: "/admin/content" },
        { path: "users", name: "AdminUsers", component: AdminUsers },
        { path: "settings", name: "AdminSettings", component: AdminSettings },
        { path: "content", name: "AdminContent", component: AdminContent },
      ],
    },
  ],
});

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore();

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next("/login");
  } else if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next("/");
  } else {
    next();
  }
});

export default router;
