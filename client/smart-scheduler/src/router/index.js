import { createRouter, createWebHistory } from '@ionic/vue-router';
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Settings from '../views/Settings.vue'
import Home from '../views/Home.vue'
import Tasks from '../views/Tasks.vue'
import Habits from '../views/Habits.vue'
import Pomodoro from '../views/Pomodoro.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings
  },
  {
    path: '/home',
    name: 'Home',
    component: Home
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: Tasks
  },
  {
    path: '/habits',
    name: 'Habits',
    component: Habits
  },
  {
    path: '/pomodoro',
    name: 'Pomodoro',
    component: Pomodoro
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
