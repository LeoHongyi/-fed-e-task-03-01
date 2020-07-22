class Watcher {
  /**
   * @param {} vm vue实例
   * @param {} key data中的属性名称
   * @param {} cb 回调函数，用来更新视图
   */
  constructor(vm, key, cb) {
      this.vm = vm;
      this.key = key;
      this.cb = cb;

      Dep.target = this;
      // vm[key]就是访问data中的属性，例如访问msg。
      // 访问msg，就会触发getter，
      this.oldVal = vm[key];
      // Dep.target置空，防止在getter中重复添加
      Dep.target = null;
  }

  /**
   * 更新视图
   */
  update() {
      const newVal = this.vm[this.key];
      if (this.oldVal === newVal) {
          return;
      }
      this.cb(newVal);
  }
}