import Vue from 'vue'
// import VueRouter from 'vue-router'
import VueRouter from '../vueRouter/index'
import Home from '../pages/index.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/about',
    name: 'About',
    component: () => import(/* webpackChunkName: "about" */ '../pages/about.vue')
  },
]

const router = new VueRouter({
  mode: 'hash',
  routes
})

export default router