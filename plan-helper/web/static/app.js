/**
 * plan-helper Web UI - Vue 3 Application
 * Modern plan management interface
 */

const { createApp, ref, computed, onMounted, watch, reactive } = Vue;

const app = createApp({
    setup() {
        // ==========================================
        // State
        // ==========================================
        const currentView = ref('dashboard');
        const sidebarCollapsed = ref(false);
        const showCreatePlan = ref(false);
        const showAddLog = ref(false);
        const showImport = ref(false);
        const showSettings = ref(false);

        const plans = ref([]);
        const selectedPlan = ref(null);
        const planDetail = ref(null);
        const planProgress = ref(null);
        const planConflicts = ref(null);
        const templates = ref([]);
        const suggestions = ref(null);

        // Calendar state
        const calendarDate = ref(new Date());
        const calendarDays = ref([]);

        // Form state
        const newPlan = reactive({ name: '', date: '' });
        const newLog = reactive({ taskId: 'base', content: '', time: '' });
        const importJson = ref('');

        // Toast
        const toast = reactive({ show: false, message: '', type: 'success' });

        // ==========================================
        // Computed
        // ==========================================
        const totalTasks = computed(() =>
            plans.value.reduce((sum, p) => sum + (p.total_tasks || 0), 0)
        );

        const completedTasks = computed(() =>
            plans.value.reduce((sum, p) => sum + (p.completed_tasks || 0), 0)
        );

        const overallProgress = computed(() => {
            if (totalTasks.value === 0) return 0;
            return Math.round(completedTasks.value / totalTasks.value * 100);
        });

        const calendarTitle = computed(() => {
            const d = calendarDate.value;
            return `${d.getFullYear()}年${d.getMonth() + 1}月`;
        });

        const allTasks = computed(() => {
            if (!planDetail.value || !planDetail.value.sections) return [];
            const tasks = [];
            for (const section of planDetail.value.sections) {
                for (const task of section.tasks) {
                    if (task.index > 0 && task.is_active) {
                        tasks.push({ ...task, sectionLetter: section.letter });
                    }
                }
            }
            return tasks;
        });

        const weekdayRatio = computed(() => {
            if (!suggestions.value) return 50;
            const total = suggestions.value.weekday_plans + suggestions.value.weekend_plans;
            if (total === 0) return 50;
            return Math.round(suggestions.value.weekday_plans / total * 100);
        });

        // ==========================================
        // API Helpers
        // ==========================================
        async function apiGet(url) {
            try {
                const resp = await fetch(url);
                return await resp.json();
            } catch (e) {
                showToast('网络错误: ' + e.message, 'error');
                return null;
            }
        }

        async function apiPost(url, data) {
            try {
                const resp = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                });
                return await resp.json();
            } catch (e) {
                showToast('网络错误: ' + e.message, 'error');
                return null;
            }
        }

        async function apiPut(url, data) {
            try {
                const resp = await fetch(url, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                });
                return await resp.json();
            } catch (e) {
                showToast('网络错误: ' + e.message, 'error');
                return null;
            }
        }

        async function apiDelete(url) {
            try {
                const resp = await fetch(url, { method: 'DELETE' });
                return await resp.json();
            } catch (e) {
                showToast('网络错误: ' + e.message, 'error');
                return null;
            }
        }

        // ==========================================
        // Data Loading
        // ==========================================
        async function loadPlans() {
            const resp = await apiGet('/api/plans');
            if (resp && resp.success) {
                plans.value = resp.data.plans || [];
            }
        }

        async function loadTemplates() {
            const resp = await apiGet('/api/templates');
            if (resp && resp.success) {
                templates.value = resp.data.templates || [];
            }
        }

        async function loadSuggestions() {
            const resp = await apiGet('/api/suggestions');
            if (resp && resp.success) {
                suggestions.value = resp.data.suggestion;
            }
        }

        async function openPlan(planId) {
            selectedPlan.value = plans.value.find(p => p.id === planId);

            // Load full plan data
            const fullResp = await apiGet(`/api/plans/${planId}/full`);
            if (fullResp && fullResp.success) {
                planDetail.value = fullResp.data;
            }

            // Load progress
            const progressResp = await apiGet(`/api/plans/${planId}/progress`);
            if (progressResp && progressResp.success) {
                planProgress.value = progressResp.data;
            }

            // Check conflicts
            const conflictResp = await apiGet(`/api/plans/${planId}/conflicts`);
            if (conflictResp && conflictResp.success) {
                planConflicts.value = conflictResp.data;
            }

            currentView.value = 'detail';
        }

        // ==========================================
        // Actions
        // ==========================================
        function navigate(view) {
            currentView.value = view;
            if (view === 'templates') loadTemplates();
            if (view === 'suggestions') loadSuggestions();
            if (view === 'calendar') buildCalendar();
            if (view === 'dashboard') loadPlans();
        }

        async function createPlan() {
            const data = { name: newPlan.name || undefined };
            if (newPlan.date) {
                const [y, m, d] = newPlan.date.split('-').map(Number);
                data.date = [y, m, d];
            }
            const resp = await apiPost('/api/plans', data);
            if (resp && resp.success) {
                showToast('计划创建成功', 'success');
                showCreatePlan.value = false;
                newPlan.name = '';
                newPlan.date = '';
                await loadPlans();
                if (resp.data.id) {
                    openPlan(resp.data.id);
                }
            } else {
                showToast(resp?.error || '创建失败', 'error');
            }
        }

        async function applyTemplate(templateId) {
            const resp = await apiPost('/api/plans/from-template', { template_id: templateId });
            if (resp && resp.success) {
                showToast('已从模板创建计划', 'success');
                await loadPlans();
                if (resp.data.id) {
                    openPlan(resp.data.id);
                }
            } else {
                showToast(resp?.error || '创建失败', 'error');
            }
        }

        async function copyYesterday() {
            const resp = await apiPost('/api/plans/copy-yesterday', {});
            if (resp && resp.success) {
                showToast('已复制昨日计划', 'success');
                await loadPlans();
                if (resp.data.id) {
                    openPlan(resp.data.id);
                }
            } else {
                showToast(resp?.error || '未找到昨日计划', 'error');
            }
        }

        async function completeTask(task, section) {
            if (!planDetail.value) return;
            const now = new Date();
            const resp = await apiPost(`/api/plans/${planDetail.value.id}/complete`, {
                task_id: `${section.letter}${task.index}`,
                day: 0,
                time: [now.getHours(), now.getMinutes()],
            });
            if (resp && resp.success) {
                showToast(`任务 ${section.letter}${task.index} 已完成`, 'success');
                // Reload plan detail
                await openPlan(planDetail.value.id);
                await loadPlans();
            } else {
                showToast(resp?.error || '操作失败', 'error');
            }
        }

        function toggleTaskComplete(task, section) {
            if (!task.finish) {
                completeTask(task, section);
            }
        }

        async function submitLog() {
            if (!planDetail.value) return;
            const data = {
                day: 0,
                task_id: newLog.taskId,
                content: newLog.content,
                time: newLog.time || 'acc',
            };
            const resp = await apiPost(`/api/plans/${planDetail.value.id}/logs`, data);
            if (resp && resp.success) {
                showToast('进展已记录', 'success');
                showAddLog.value = false;
                newLog.taskId = 'base';
                newLog.content = '';
                newLog.time = '';
                await openPlan(planDetail.value.id);
            } else {
                showToast(resp?.error || '记录失败', 'error');
            }
        }

        function quickLog(planId) {
            selectedPlan.value = plans.value.find(p => p.id === planId);
            openPlan(planId).then(() => {
                showAddLog.value = true;
            });
        }

        async function deletePlan(planId) {
            if (!confirm('确定要删除此计划吗？')) return;
            const resp = await apiDelete(`/api/plans/${planId}`);
            if (resp && resp.success) {
                showToast('计划已删除', 'success');
                currentView.value = 'dashboard';
                await loadPlans();
            } else {
                showToast(resp?.error || '删除失败', 'error');
            }
        }

        async function exportPlan(planId) {
            const resp = await apiGet(`/api/plans/${planId}/full`);
            if (resp && resp.success) {
                const json = JSON.stringify(resp.data, null, 2);
                const blob = new Blob([json], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `plan_${planId}.json`;
                a.click();
                URL.revokeObjectURL(url);
                showToast('导出成功', 'success');
            }
        }

        async function importPlan() {
            try {
                JSON.parse(importJson.value); // Validate JSON
            } catch (e) {
                showToast('JSON 格式无效', 'error');
                return;
            }
            const resp = await apiPost('/api/plans/import', { json: importJson.value });
            if (resp && resp.success) {
                showToast('导入成功', 'success');
                showImport.value = false;
                importJson.value = '';
                await loadPlans();
            } else {
                showToast(resp?.error || '导入失败', 'error');
            }
        }

        async function createBackup() {
            const resp = await apiPost('/api/backup', {});
            if (resp && resp.success) {
                showToast(`备份成功 (${resp.data.plan_count} 个计划)`, 'success');
            } else {
                showToast('备份失败', 'error');
            }
        }

        // ==========================================
        // Calendar
        // ==========================================
        function buildCalendar() {
            const d = calendarDate.value;
            const year = d.getFullYear();
            const month = d.getMonth();

            const firstDay = new Date(year, month, 1);
            const lastDay = new Date(year, month + 1, 0);

            // Adjust to Monday start
            let startDow = firstDay.getDay();
            if (startDow === 0) startDow = 7;

            const days = [];
            const today = new Date();

            // Previous month days
            const prevMonthLast = new Date(year, month, 0).getDate();
            for (let i = startDow - 1; i > 0; i--) {
                days.push({
                    day: prevMonthLast - i + 1,
                    dateStr: `${year}-${month}-${prevMonthLast - i + 1}`,
                    currentMonth: false,
                    isToday: false,
                    hasPlan: false,
                });
            }

            // Current month days
            for (let i = 1; i <= lastDay.getDate(); i++) {
                const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
                const isToday = today.getFullYear() === year && today.getMonth() === month && today.getDate() === i;

                // Check if any plan matches this date
                const hasPlan = plans.value.some(p => {
                    if (p.date && p.date.length >= 3) {
                        return p.date[0] === year && p.date[1] === month + 1 && p.date[2] === i;
                    }
                    return false;
                });

                days.push({
                    day: i,
                    dateStr,
                    currentMonth: true,
                    isToday,
                    hasPlan,
                    planClass: hasPlan ? 'has-plan' : '',
                });
            }

            // Next month days (fill to 42 = 6 rows)
            const remaining = 42 - days.length;
            for (let i = 1; i <= remaining; i++) {
                days.push({
                    day: i,
                    dateStr: `${year}-${month + 2}-${i}`,
                    currentMonth: false,
                    isToday: false,
                    hasPlan: false,
                });
            }

            calendarDays.value = days;
        }

        function calendarPrev() {
            const d = new Date(calendarDate.value);
            d.setMonth(d.getMonth() - 1);
            calendarDate.value = d;
            buildCalendar();
        }

        function calendarNext() {
            const d = new Date(calendarDate.value);
            d.setMonth(d.getMonth() + 1);
            calendarDate.value = d;
            buildCalendar();
        }

        function onCalendarDayClick(day) {
            if (!day.currentMonth) return;
            // Find plan for this day
            const plan = plans.value.find(p => {
                if (p.date && p.date.length >= 3) {
                    return p.date[2] === day.day;
                }
                return false;
            });
            if (plan) {
                openPlan(plan.id);
            }
        }

        // ==========================================
        // Drag & Drop
        // ==========================================
        function onDragStart(event, plan) {
            event.dataTransfer.setData('text/plain', plan.id);
            event.target.classList.add('dragging');
        }

        function onDrop(event, targetPlan) {
            event.preventDefault();
            const draggedId = event.dataTransfer.getData('text/plain');
            event.target.classList.remove('dragging');
            // Reorder plans
            const draggedIdx = plans.value.findIndex(p => p.id === parseInt(draggedId));
            const targetIdx = plans.value.findIndex(p => p.id === targetPlan.id);
            if (draggedIdx !== -1 && targetIdx !== -1 && draggedIdx !== targetIdx) {
                const [dragged] = plans.value.splice(draggedIdx, 1);
                plans.value.splice(targetIdx, 0, dragged);
            }
        }

        // ==========================================
        // Helpers
        // ==========================================
        function formatDate(dateArr) {
            if (!dateArr || dateArr.length < 3) return '未知';
            return `${dateArr[0]}/${String(dateArr[1]).padStart(2, '0')}/${String(dateArr[2]).padStart(2, '0')}`;
        }

        function formatLogTime(timeArr) {
            if (!timeArr || timeArr.length < 2) return '';
            const h = timeArr[0];
            const m = timeArr[1];
            if (m === 99) {
                return `${h > 12 ? h - 12 : h || 12}${h >= 12 ? 'pm' : 'am'}`;
            }
            return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
        }

        function getProgressColor(pct) {
            if (pct >= 80) return 'green';
            if (pct >= 40) return 'blue';
            return 'orange';
        }

        function getPriorityClass(plan) {
            if (plan.progress_percentage >= 80) return 'low';
            if (plan.progress_percentage >= 40) return 'medium';
            return 'high';
        }

        function getDetailProgress() {
            if (!planProgress.value) return 0;
            return planProgress.value.progress_percentage;
        }

        function showToast(message, type = 'success') {
            toast.message = message;
            toast.type = type;
            toast.show = true;
            setTimeout(() => { toast.show = false; }, 3000);
        }

        // ==========================================
        // Lifecycle
        // ==========================================
        onMounted(async () => {
            await loadPlans();
            buildCalendar();
        });

        return {
            // State
            currentView, sidebarCollapsed, showCreatePlan, showAddLog, showImport, showSettings,
            plans, selectedPlan, planDetail, planProgress, planConflicts,
            templates, suggestions,
            calendarDate, calendarDays,
            newPlan, newLog, importJson,
            toast,
            // Computed
            totalTasks, completedTasks, overallProgress,
            calendarTitle, allTasks, weekdayRatio,
            // Navigation
            navigate, openPlan,
            // Actions
            createPlan, applyTemplate, copyYesterday,
            completeTask, toggleTaskComplete, submitLog,
            quickLog, deletePlan, exportPlan, importPlan,
            createBackup, loadSuggestions,
            // Calendar
            calendarPrev, calendarNext, onCalendarDayClick,
            // Drag & Drop
            onDragStart, onDrop,
            // Helpers
            formatDate, formatLogTime, getProgressColor,
            getPriorityClass, getDetailProgress,
        };
    }
});

app.mount('#app');
