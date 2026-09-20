# to-dos 前端模块

Vue 3 + TypeScript + Tailwind CSS 实现的待办事项界面

## 技术栈

- Vue 3 (Composition API)
- TypeScript
- Tailwind CSS
- Pinia (状态管理)
- Lucide Vue Next (图标)

## 目录结构

```
src/
├── components/        # 可复用组件
│   ├── TodoItem.vue
│   ├── TodoForm.vue
│   ├── CategorySidebar.vue
│   ├── FilterBar.vue
│   └── ...
├── views/            # 页面视图
│   └── TodosView.vue
├── stores/           # Pinia 状态管理
│   └── todos.ts
├── types/            # TypeScript 类型定义
│   └── index.ts
└── styles/           # 样式文件
    └── main.css
```

## 开发

```bash
npm install
npm run dev
```

## 构建

```bash
npm run build
```
