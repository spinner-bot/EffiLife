async function refresh() {
  const data = await EffiLife.request('data.read')
  const plans = data.plans.filter(plan => !plan.archivedAt).length
  const todos = data.todos.filter(todo => todo.status === 'pending').length
  EffiLife.render({
    html: '<main><small>EFFILIFE · EXTENSION EXAMPLE</small><h1>Life at a glance</h1><p>' + plans + ' active plans · ' + todos + ' pending to-dos</p><nav><button data-action="plans">Open plans</button><button data-action="refresh">Refresh</button></nav></main>',
    css: 'main{padding:24px;color:#203045;background:#f7f9fc;min-height:320px;font-family:system-ui,sans-serif}h1{font-size:24px;line-height:1.3}small{font-size:10px;letter-spacing:1px}p{margin:24px 0}nav{display:flex;gap:12px}button{padding:10px 14px;border:1px solid #cbd5e1;border-radius:8px;background:white;color:#233044;cursor:pointer}',
  })
}
EffiLife.onMount(refresh)
EffiLife.onChange(refresh)
EffiLife.onAction(async event => {
  if (event.name === 'plans') await EffiLife.request('navigate', '/plans')
  if (event.name === 'refresh') await refresh()
})

