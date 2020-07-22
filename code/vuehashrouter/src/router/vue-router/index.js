let _Vue = null
export default class VueRouter {
  // options就是传入的路由规则
  constructor (options) {
    this.options = options
    // this.routeMap是对象，键是路由地址，键对应的值是路由地址对应的组件
    this.routeMap = {}
    // this.data是响应式对象，由vue.observable()创建的，可以直接用在渲染函数或者计算属性里面
    this.data = _Vue.observable({
      // current是当前路由地址
      current: '/'
    })
    this.mode = this.options.mode
  }

  static install (Vue) {
    // 1. 判断当前插件是否已经被安装
    if (VueRouter.install.installed) {
      return
    }
    VueRouter.install.installed = true
    // 2. 把Vue构造函数记录到全局变量
    _Vue = Vue
    // 3. 把创建Vue实例时候传入的router对象注入到Vue实例上
    // 全局混入
    _Vue.mixin({
      beforeCreate () {
        // this就是创建的Vue实例
        // this.$options就是传入Vue实例的选项，选项中会传入router
        if (this.$options.router) {
          _Vue.prototype.$router = this.$options.router
          this.$options.router.init()
        }
      }
    })
  }

  init () {
    this.createRouteMap()
    this.initComponents(_Vue)
    this.initEvent()
  }

  createRouteMap () {
    // 遍历所有的路由规则，把路由规则解析成键值对的形式，存储到routeMap中
    this.options.routes.map(route => {
      this.routeMap[route.path] = route.component
    })
  }

  initComponents (Vue) {
    // Vue.component()用来创建一个组件
    Vue.component('router-link', {
      props: {
        // 向router-link组件的to属性传入参数
        to: String
      },
      // 运行时版本vue不带编译器，无法编译template模板
      // template:'<a :href="to"><slot></slot></a>'

      // 运行时版本vue，使用render()函数
      render (h) {
        // 第一个参数是要创建的元素
        // 第二个参数是配置元素的属性
        // 第三个参数是创建的元素的子元素，是数组的形式。当前插槽没有起名字，所以是默认插槽。
        return h('a', {
          attrs: {
            href: this.to // to的值是视图中<router-link to="/">Home</router-link>传递进来的
          },
          on: {
            click: this.clickHandler
          }
        }, [this.$slots.default])
      },
      methods: {
        clickHandler (e) {
          // history.pushState({}, '', this.to)
          location.hash = this.to
          // this是router-link组件，router-link组件是vue实例
          //  _Vue.mixin中用_Vue.prototype.$router = this.$options.router;把VueRouter实例注入到_Vue实例中了。而router-link是vue实例，所以可以用this.$router获取到$router。
          // 又因为constructor()构造函数中，this.data中的this代表VueRouter实例，所以可以获取this.$router.data
          this.$router.data.current = this.to
          e.preventDefault()
        }
      }
    })

    const self = this // this就是vueRouter
    // 创建router-view组件
    Vue.component('router-view', {
      render (h) {
        // 根据当前路由地址从routeMap中获取当前路由地址对应的组件
        const component = self.routeMap[self.data.current]
        // 用h()函数把组件转换成虚拟dom，返回
        return h(component)
      }
    })
  }

  initEvent () {
    // Hash 模式，把 URL 中#后面的内容作为路由地址，可以直接通过 location.hash 来切换路由中的地址
    // 初始加载页面是，hash无值，因此要先设置hash值为"/"
    if (!location.hash) {
      location.hash = '/' // 首次加载页面，跳转到home页面
    }
    window.addEventListener('hashchange', () => {
      this.data.current = window.location.hash.slice(1)
    })
  }
}