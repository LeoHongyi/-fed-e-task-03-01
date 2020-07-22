# -fed-e-task-03-01
## 一、简答题

### 1、当我们点击按钮的时候动态给 data 增加的成员是否是响应式数据，如果不是的话，如果把新增成员设置成响应式数据，它的内部原理是什么。

```js
let vm = new Vue({
  el: '#el'
  data: {
    o: 'object',
    dog: {}
  },
  method: {
    clickHandler () {
      // 该 name 属性是否是响应式的
      this.dog.name = 'Trump'
    }
  }
})
```
1. 给dog对象添加的新属性不是响应式的。

2. 可以使用 Vue.set(object, propertyName, value) 方法向嵌套对象添加响应式 property，Vue 不允许动态添加根级别的响应式 property。因此可以使用vm.$set()方法把本题中的name转化成响应式的。

3. 因为 Object.defineProperty() 无法检测 property 的添加或移除。对于已经创建的实例，Vue 不允许动态添加根级别的 property。但是可以使用 Vue.set(sameObj, propertyName, value) 方法向嵌套对象添加响应式 property 
 ```js
Vue.set(this.data, 'name', 'Trump')

// 或实例方法
this.
 ```

 ### 2、请简述 Diff 算法的执行过程
 - 新老节点都有 text ，且不相等

  - 设置新节点对应 DOM 元素的 textContent

- 只有老节点有 text

  - 清空对应 DOM 元素的 textContent

- 只有新节点有 text

  - 设置新节点对应 DOM 元素的 textContent

- 新老节点都有 children ，且不相等

  - 调用 `updateChildren()`
  - 对比子节点，并更新子节点差异

- 只有老节点有 Children

  - 移除所有子节点

- 只有新节点有 Children

  - 天加所有子节点

`updateChildren` 是 diff 算法的核心：

- 对同级别的子节点依次比较，然后再找下一级别的节点比较

- 在进行同级别节点比较的时候，首先会对新老节点数组的开始和结尾节点设置标记索引，遍历过程中移动索引

- 在对开始和结束节点比较时，总共有四种情况

  - oldStartVnode / newStartVnode （旧开始节点 / 新开始节点）
  - oldEndVnode / newEndVnode （旧结束节点 / 新结束节点）
  - oldStartVnode / newEndVnode （旧开始节点 / 新结束节点）
  - oldEndVnode / newStartVnode （旧结束节点 / 新开始节点）

- 开始节点和结束节点比较，这两种情况类似

  - oldStartVnode / newStartVnode （旧开始节点 / 新开始节点）
  - oldEndVnode / newEndVnode （旧结束节点 / 新结束节点）

- 如果 oldStartVnode 和 newStartVnode 是 sameVnode

  - 调用 `patchVnode()` 对比和更新节点
  - 把旧开始和新开始索引往后移动

- 如果 oldStartVnode 和 newEndVnode 是 sameVnode

  - 调用 `patchVnode()` 对比和更新节点
  - 把 oldStartVnode 对应的 DOM 元素移动到最右边
  - 更新索引

- 如果 oldEndVnode 和 newStartVnode 是 sameVnode

  - 调用 `patchVnode()` 对比和更新节点
  - 把 oldEndVnode 对应的 DOM 元素移动到最左边边

- 如果不是以上四种情况

  - 遍历新节点，使用 newStartVnode 的 key 在老节点数组中找相同节点
  - 如果没有找到，说明 newStartVnode 是新节点

    - 创建新节点对应的 DOM 元素，插入到 DOM 树中

  - 如果找到了

    - 判断新节点和找到的老节点是否相同
    - 如果不相同，说明节点被修改了

      - 重新创建对应的 DOM 元素，插入到 DOM 树中

    - 如果相同，把找到的老节点移动到左边

- 循环结束

  - 当老节点的所有子节点先遍历完（oldStartIdx > oldEndIdx）
  - 当新节点的所有子节点先遍历完（newStartIdx > newEndIdx）

- 如果老节点的数组优先遍历完，说明新节点有剩余，把剩余节点插入到对应位置
- 如果新节点的数组优先遍历完，说明老节点有剩余，把剩余节点删除


## 二、编程题

### 1、模拟 VueRouter 的 hash 模式的实现，实现思路和 History 模式类似，把 URL 中的 # 后面的内容作为路由的地址，可以通过 hashchange 事件监听路由地址的变化。
在vuehashrouter

### 2、在模拟 Vue.js 响应式源码的基础上实现 v-html 指令，以及 v-on 指令
在minivue

### 3、参考 Snabbdom 提供的电影列表的示例，利用Snabbdom 实现类似的效果，如
