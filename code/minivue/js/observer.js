class Observer {
  constructor(data) {
      this.walk(data);
  }

  walk(data) {
      // 1. 判断data是否为对象
      if (!data || typeof data !== "object") {
          return;
      }
      // 2. 遍历data对象的所有属性
      Object.keys(data).forEach(key => {
          this.defineReactive(data, key, data[key]);
      });
  }

  defineReactive(obj, key, val) {
      const that = this;
      const dep = new Dep();
      // 如果val是对象，那么把val中的属性也要转换成getter/setter的形式
      this.walk(val);
      Object.defineProperty(obj, key, {
          configurable: true,
          enumerable: true,
          get() {
              // 这里dep是从外部函数引用的，因此形成了闭包。
              // 所以针对每一个属性，只new一个dep
              Dep.target && dep.addSub(Dep.target);
              // 这里不能 return obj[key],访问obj[key]又会触发obj的get()，然后又访问obj[key]，再次触发obj的get()。最终导致栈溢出。
              // 同时这里val是在闭包内，因此val这个局部变量不会被释放。也可以看下浏览器的scope中closure验证
              return val;
          },
          set(newVal) {
              //console.log("this:",this);
              
              if (val === newVal) {
                  return;
              }
              val = newVal;
              // 如果这里直接写this，this是指向data的。
              //this.walk(newVal);
              // 当newVal是对象。本例子中页面上msg改为msg = {test:'hello'}
              that.walk(newVal);
              console.log(dep);
              
              // 发送通知
              dep.notify();
          }
      });
  }
}