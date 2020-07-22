/** @type import('vue-router').RouteConfig[] */
const routes = [
  {
    path: '/',
    component: () =>
      import(/* webpackChunkName: 'index' */ '../pages/Index.vue')
  },
  {
    path: '/about',
    component: () =>
      import(/* webpackChunkName: 'about' */ '../pages/About.vue')
  }
]

export default routes