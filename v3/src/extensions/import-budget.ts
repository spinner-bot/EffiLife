import defaults from '../../shared/import-budgets.json'
import { requireCondition } from '../domain/errors'

/** Runtime processing policy; not a limit encoded in the package format.
 * Platform adapters may supply a budget appropriate for their memory budget.
 */
export type ImportBudget = typeof defaults
export const importBudget: Readonly<ImportBudget> = Object.freeze({ ...defaults })
export function checkImportInput(bytes: number, budget: ImportBudget = importBudget): void {
  requireCondition(Number.isSafeInteger(bytes) && bytes >= 0 && bytes <= budget.maxInputBytes, 'archive.importBudget')
}
