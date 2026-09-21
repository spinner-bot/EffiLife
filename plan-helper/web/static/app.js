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
        const showEditPlan = ref(false);
        const backupLoading = ref(false);

        const plans = ref([]);
        const selectedPlan = ref(null);
        const planDetail = ref(null);
        const planProgress = ref(null);
        const planConflicts = ref(null);
        const templates = ref([]);
        const suggestions = ref(null);
        const backups = ref([]);
        const editPlan = ref(null);

        // Form state
        const newPlan = reactive({ name: '', date: todayInput(), sections: [] });
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
            if (view === 'dashboard') loadPlans();
        }

        function openCreatePlan() {
            newPlan.name = '';
            newPlan.date = todayInput();
            newPlan.sections = [newSection()];
            showCreatePlan.value = true;
        }

        async function createPlan() {
            if (!newPlan.name.trim()) {
                showToast('请输入计划名称', 'error');
                return;
            }
            if (!newPlan.date) {
                showToast('请选择计划日期', 'error');
                return;
            }
            const data = {
                name: newPlan.name.trim(),
                date: dateInputToTuple(newPlan.date),
                sections: newPlan.sections.map(section => ({
                    name: section.name.trim(),
                    info: section.info.trim(),
                    tasks: section.tasks
                        .filter(task => task.content.trim())
                        .map(task => ({ content: task.content.trim(), time_minutes: Number(task.time_minutes) || 0 }))
                })).filter(section => section.name),
            };
            const resp = await apiPost('/api/plans', data);
            if (resp && resp.success) {
                showToast('计划创建成功', 'success');
                showCreatePlan.value = false;
                newPlan.name = '';
                newPlan.date = todayInput();
                newPlan.sections = [];
                await loadPlans();
                if (resp.data.id) {
                    openPlan(resp.data.id);
                }
            } else {
                showToast(resp?.error || '创建失败', 'error');
            }
        }

        function startEditPlan() {
            if (!planDetail.value) return;
            editPlan.value = {
                id: planDetail.value.id,
                name: planDetail.value.name || '',
                date: tupleToDateInput(planDetail.value.date),
                sections: JSON.parse(JSON.stringify(planDetail.value.sections || [])),
            };
            showEditPlan.value = true;
        }

        function closeEditPlan() {
            showEditPlan.value = false;
            editPlan.value = null;
        }

        async function saveEditPlan() {
            if (!editPlan.value || !editPlan.value.name.trim() || !editPlan.value.date) {
                showToast('计划名称和日期不能为空', 'error');
                return;
            }
            const meta = await apiPut(`/api/plans/${editPlan.value.id}`, {
                name: editPlan.value.name.trim(),
                date: dateInputToTuple(editPlan.value.date),
            });
            if (!meta || !meta.success) {
                showToast(meta?.error || '计划信息保存失败', 'error');
                return;
            }
            for (const section of editPlan.value.sections) {
                let sectionResp;
                if (section.index === undefined) {
                    sectionResp = await apiPost(`/api/plans/${editPlan.value.id}/sections`, {
                        name: section.name,
                        info: section.info,
                    });
                    if (sectionResp?.success) {
                        section.index = sectionResp.data.section_index;
                        section.letter = String.fromCharCode(65 + section.index);
                    }
                } else {
                    sectionResp = await apiPut(`/api/plans/${editPlan.value.id}/sections/${section.index}`, {
                        name: section.name,
                        info: section.info,
                    });
                }
                if (!sectionResp || !sectionResp.success) {
                    showToast(sectionResp?.error || '章节保存失败', 'error');
                    return;
                }
                for (const task of section.tasks || []) {
                    if (!task.is_active) continue;
                    let taskResp;
                    if (task.index === undefined) {
                        taskResp = await apiPost(`/api/plans/${editPlan.value.id}/tasks`, {
                            section_index: section.index,
                            content: task.content,
                            time_minutes: Number(task.time_minutes) || 0,
                        });
                    } else {
                        taskResp = await apiPut(`/api/plans/${editPlan.value.id}/tasks/${section.letter}${task.index}`, {
                            content: task.content,
                            time_minutes: Number(task.time_minutes) || 0,
                        });
                    }
                    if (!taskResp || !taskResp.success) {
                        showToast(taskResp?.error || '任务保存失败', 'error');
                        return;
                    }
                }
            }
            closeEditPlan();
            showToast('计划修改已保存', 'success');
            await loadPlans();
            await openPlan(planDetail.value.id);
        }

        async function removeEditSection(section) {
            if (section.index === undefined) return;
            if (!confirm(`确定删除章节“${section.name}”吗？`)) return;
            const resp = await apiDelete(`/api/plans/${editPlan.value.id}/sections/${section.index}`);
            if (resp && resp.success) {
                editPlan.value.sections = editPlan.value.sections.filter(item => item !== section);
                showToast('章节已删除', 'success');
                await openPlan(editPlan.value.id);
                startEditPlan();
            } else showToast(resp?.error || '删除章节失败', 'error');
        }

        async function removeEditTask(task) {
            if (!confirm(`确定删除任务“${task.content}”吗？`)) return;
            const section = editPlan.value.sections.find(item => item.tasks.includes(task));
            if (!section) return;
            const resp = await apiDelete(`/api/plans/${editPlan.value.id}/tasks/${section.letter}${task.index}`);
            if (resp && resp.success) {
                task.is_active = false;
                showToast('任务已删除', 'success');
            } else showToast(resp?.error || '删除任务失败', 'error');
        }

        function addEditSection() {
            editPlan.value.sections.push({ index: undefined, letter: '?', name: '新章节', info: '', tasks: [] });
        }

        function addEditTask(section) {
            section.tasks.push({ index: undefined, content: '新任务', time_minutes: 30, is_active: true });
        }

        function addNewSection() {
            newPlan.sections.push(newSection());
        }

        function removeNewSection(index) {
            newPlan.sections.splice(index, 1);
        }

        function addNewTask(sectionIndex) {
            newPlan.sections[sectionIndex].tasks.push({ content: '', time_minutes: 30 });
        }

        function removeNewTask(sectionIndex, taskIndex) {
            newPlan.sections[sectionIndex].tasks.splice(taskIndex, 1);
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
            backupLoading.value = true;
            const resp = await apiPost('/api/backup', {});
            if (resp && resp.success) {
                showToast(`备份成功 (${resp.data.plan_count} 个计划)`, 'success');
                await loadBackups();
            } else {
                showToast('备份失败', 'error');
            }
            backupLoading.value = false;
        }

        async function loadBackups() {
            const resp = await apiGet('/api/backups');
            if (resp && resp.success) backups.value = resp.data.backups || [];
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

        function todayInput() {
            const now = new Date();
            return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
        }

        function dateInputToTuple(value) {
            return value.split('-').map(Number);
        }

        function tupleToDateInput(value) {
            if (!value || value.length < 3) return todayInput();
            return `${value[0]}-${String(value[1]).padStart(2, '0')}-${String(value[2]).padStart(2, '0')}`;
        }

        function newSection() {
            return { name: '', info: '', tasks: [{ content: '', time_minutes: 30 }] };
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
            await loadBackups();
        });

        return {
            // State
            currentView, sidebarCollapsed, showCreatePlan, showAddLog, showImport, showSettings, showEditPlan,
            plans, selectedPlan, planDetail, planProgress, planConflicts,
            templates, suggestions,
            backups, backupLoading, editPlan, newPlan, newLog, importJson,
            toast,
            // Computed
            totalTasks, completedTasks, overallProgress,
            allTasks, weekdayRatio,
            // Navigation
            navigate, openPlan,
            // Actions
            openCreatePlan, createPlan, applyTemplate, copyYesterday,
            startEditPlan, closeEditPlan, saveEditPlan,
            addEditSection, addEditTask, removeEditSection, removeEditTask,
            addNewSection, removeNewSection, addNewTask, removeNewTask,
            completeTask, toggleTaskComplete, submitLog,
            quickLog, deletePlan, exportPlan, importPlan,
            createBackup, loadBackups, loadSuggestions,
            // Drag & Drop
            onDragStart, onDrop,
            // Helpers
            formatDate, formatLogTime, getProgressColor,
            getPriorityClass, getDetailProgress,
        };
    }
});

app.mount('#app');
