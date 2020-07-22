class Vue {
  constructor(options) {
      // 1. 通过属性保存选项的数据
      this.$options = options || {};
      this.$data = options.data || {};
      this.$methods = options.methods || {};
      // 判断options.el是否是选择器还是dom对象
      this.$el = typeof options.el === "string" ? document.querySelector(options.el) : options.el;

      // 2. 把data中的成员转换成getter/setter，注入到vue实例中
      this._proxyData(this.$data);

      // 3. 调用observer对象，把data中的属性转换成getter/setter形式
      new Observer(this.$data);

      // 4. 调用compiler对象，解析指令和差值表达式
      new Compiler(this);
  }

  _proxyData(data) {
      Object.keys(data).forEach(key => [
          // 把data中的属性注入到vue实例中，vue实例代理data中的属性
          Object.defineProperty(this, key, {
              enumerable: true,
              configurable: true,
              get() {
                  return data[key];
              },
              set(newVal) {
                  if (data[key] === newVal) {
                      return;
                  }
                  data[key] = newVal;
              }
          })
      ]);
  }
}