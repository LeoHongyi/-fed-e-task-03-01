class Compiler {
  constructor(vm) {
      // 在vue.js的构造函数中已经把el赋值给了vue.$el
      this.el = vm.$el;
      this.vm = vm;
      this.compile(this.el);
  }

  // 编译模板，处理文本节点和元素节点
  compile(el) {
      const childNodes = el.childNodes; // 这个获取的只是第一层的子节点
      for (const node of childNodes) {
          if (this.isTextNode(node)) {
              this.compileText(node);
          } else if (this.isElementNode(node)) {
              this.compileElement(node);
          }
          // 判断node节点，是否有子节点，如果有子节点，要递归调用compile
          if (node.childNodes && node.childNodes.length) {
              this.compile(node)
          }
      }
  }

  // 编译元素节点，处理指令
  compileElement(node) {
      // console.log(node.attributes);//属性节点，v-text="msg"。打印出来,存在name属性 v-text,value属性 msg
      // 遍历所有的属性节点
      const attributes = node.attributes; //获取所有属性节点
      for (const attr of attributes) {
          // console.log(attr.name, attr.value);
          let attrName = attr.name; //v-text，v-on:click
          if (this.isDirective(attrName)) {
              attrName = attrName.substr(2); // text on:click
              const key = attr.value; //msg btnFunc
              this.update(node, key, attrName);
          }
      }
  }

  /**
   * 
   * @param {} node dom元素节点
   * @param {} key data中的属性值
   * @param {} attrName v-xxx，即指令名
   */
  update(node, key, attrName) {
      let updateFn = null;
      const attrNameTemp = attrName.split(':');
      if (attrNameTemp.length > 1) {
          attrName = attrNameTemp[1];
          // 获取这个实例中的函数名即函数标识符
          updateFn = this[attrName + "Updater"]; //on:click
          updateFn && updateFn.call(this, node, this.vm.$methods[key], attrName);
      } else {
          // 获取这个实例中的函数名即函数标识符
          updateFn = this[attrName + "Updater"]; // textUpdater,modelUpdater
          // updateFn是直接调用的，因此textUpdater和modelUpdater内部的this指向不是指向Compiler
          // 因此需要用call绑定updateFn函数内部的this指向为Compiler
          updateFn && updateFn.call(this, node, this.vm[key], key);
      }
  }

  // 处理v-text指令
  textUpdater(node, value, key) {
      node.textContent = value;
      new Watcher(this.vm, key, (newValue) => {
          node.textContent = newValue;
      });
  }

  // 处理v-model指令
  modelUpdater(node, value, key) {
      // node是input，v-model是input元素中双向绑定用的
      // 设置input的值，就是通过设置input的value属性值
      node.value = value;

      new Watcher(this.vm, key, (newValue) => {
          node.value = newValue;
      });

      // 双向绑定，监听dom元素input的输入属性就行了
      node.addEventListener("input", () => {
          // 箭头函数内部没有this，或者说箭头函数没有改变this指向，因此this还是Compiler
          this.vm[key] = node.value;
      });
  }

  // 处理v-html指令
  htmlUpdater(node, value, key) {
      node.innerHTML = value;
      new Watcher(this.vm, key, (newValue) => {
          node.innerHTML = newValue;
      });
  }

  // 处理v-on:click指令
  clickUpdater(node, value, methodType) {
      window.addEventListener(methodType, () => {
          value.call(this.vm);
      });
  }

  // 编译文本节点，处理差值表达式
  compileText(node) {
      //console.dir("node:", node);
      // {{ msg }}
      // 在要提取的地方加上()
      //()在正则表达式中有分组的含义，可以获取到分组中匹配到的结果。
      const reg = /\{\{(.+?)\}\}/;
      const value = node.textContent;
      if (reg.test(value)) {
          //RegExp.$1获取第一个分组的内容，即(.+?)括号中匹配到的内容
          const key = RegExp.$1.trim();
          //console.log("key:",key);
          // vm已经代理了data中的所有属性，所以可以用this.vm[key]获取data中的属性的值 
          node.textContent = value.replace(reg, this.vm[key]);

          // 创建watcher对象，当数据改变更新视图
          new Watcher(this.vm, key, (newVal) => {
              node.textContent = newVal;
          });
      }
  }

  // 判断元素属性是否是指令
  isDirective(attrName) {
      // vue中的指令是以v-开头的
      return attrName.startsWith('v-');
  }

  // nodeType:节点的类型：1---标签(元素)；2---属性；3---文本
  // 判断节点是否是文本节点
  isTextNode(node) {
      return node.nodeType === 3;
  }

  // 判断节点是否是元素节点
  isElementNode(node) {
      return node.nodeType === 1;
  }

}