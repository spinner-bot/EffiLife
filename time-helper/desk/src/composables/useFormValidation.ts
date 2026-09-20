import { ref, reactive, computed } from 'vue'

// 单字段规则
interface FieldRule {
  required?: boolean | string       // true = 必填，string = 自定义错误文案
  min?: number                      // 最小长度/数值
  max?: number                      // 最大长度/数值
  pattern?: RegExp                  // 正则匹配
  validator?: (value: any) => boolean | string  // 自定义验证函数，true=通过，string=错误文案
}

// 规则配置
interface ValidationRules {
  [fieldName: string]: FieldRule | FieldRule[]
}

// 错误信息
interface ValidationErrors {
  [fieldName: string]: string
}

/**
 * 表单验证 composable
 * @param rules - 验证规则配置
 * @returns errors, isValid, validate, resetErrors, getFieldError
 *
 * 用法：
 * const { errors, isValid, validate } = useFormValidation({
 *   name: { required: '请输入名称', min: 2, max: 20 },
 *   email: { required: true, pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/ },
 *   age: { min: 0, max: 120, validator: (v) => v >= 18 || '必须年满18岁' }
 * })
 *
 * const valid = validate({ name: form.name, email: form.email, age: form.age })
 */
export function useFormValidation(rules: ValidationRules) {
  const errors = reactive<ValidationErrors>({})

  // 规范化规则：单个规则包装为数组
  function normalizeRules(fieldRules: FieldRule | FieldRule[]): FieldRule[] {
    return Array.isArray(fieldRules) ? fieldRules : [fieldRules]
  }

  // 验证单个字段
  function validateField(fieldName: string, value: any): string | null {
    const fieldRules = rules[fieldName]
    if (!fieldRules) return null

    const ruleList = normalizeRules(fieldRules)

    for (const rule of ruleList) {
      // required
      if (rule.required !== undefined) {
        const isEmpty =
          value === undefined ||
          value === null ||
          value === '' ||
          (typeof value === 'string' && value.trim() === '')

        if (isEmpty) {
          if (typeof rule.required === 'string') return rule.required
          return `「${fieldName}」为必填项`
        }
      }

      // 以下规则仅在有值时检查
      if (value === undefined || value === null || value === '') continue

      // min（字符串长度或数值）
      if (rule.min !== undefined) {
        const len = typeof value === 'string' ? value.length : Number(value)
        if (len < rule.min) {
          if (typeof value === 'string') {
            return `「${fieldName}」长度不能少于 ${rule.min} 个字符`
          }
          return `「${fieldName}」不能小于 ${rule.min}`
        }
      }

      // max（字符串长度或数值）
      if (rule.max !== undefined) {
        const len = typeof value === 'string' ? value.length : Number(value)
        if (len > rule.max) {
          if (typeof value === 'string') {
            return `「${fieldName}」长度不能超过 ${rule.max} 个字符`
          }
          return `「${fieldName}」不能大于 ${rule.max}`
        }
      }

      // pattern
      if (rule.pattern) {
        const str = String(value)
        if (!rule.pattern.test(str)) {
          return `「${fieldName}」格式不正确`
        }
      }

      // custom validator
      if (rule.validator) {
        const result = rule.validator(value)
        if (result !== true) {
          return typeof result === 'string' ? result : `「${fieldName}」验证失败`
        }
      }
    }

    return null
  }

  // 验证所有字段
  function validate(values: Record<string, any>): boolean {
    let valid = true
    // 清空之前的错误
    Object.keys(errors).forEach(key => delete errors[key])

    for (const fieldName of Object.keys(rules)) {
      const value = values[fieldName]
      const error = validateField(fieldName, value)
      if (error) {
        errors[fieldName] = error
        valid = false
      }
    }

    return valid
  }

  // 验证单个字段（用于实时验证）
  function validateOne(fieldName: string, value: any): string | null {
    const error = validateField(fieldName, value)
    if (error) {
      errors[fieldName] = error
    } else {
      delete errors[fieldName]
    }
    return error
  }

  // 是否有错误
  const isValid = computed(() => Object.keys(errors).length === 0)

  // 重置错误
  function resetErrors() {
    Object.keys(errors).forEach(key => delete errors[key])
  }

  // 获取某字段的错误
  function getFieldError(fieldName: string): string | undefined {
    return errors[fieldName]
  }

  return {
    errors,
    isValid,
    validate,
    validateOne,
    resetErrors,
    getFieldError,
  }
}
