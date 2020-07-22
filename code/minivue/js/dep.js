class Dep{
  constructor(){
      this.subs = [];
  }

  addSub(watcher){
      this.subs.push(watcher);
  }

  notify(){
      for (const watcher of this.subs) {
          watcher.update();
      }
  }
}