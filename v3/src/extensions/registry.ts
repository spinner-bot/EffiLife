import { DomainError } from '../domain/errors'

export class Registry<T extends { id: string | number }> {
  private readonly entries = new Map<T['id'], T>()
  register(entry: T): void {
    if (this.entries.has(entry.id)) throw new DomainError('extensions.duplicateIdentity')
    this.entries.set(entry.id, entry)
  }
  get(id: T['id']): T | undefined { return this.entries.get(id) }
  values(): T[] { return [...this.entries.values()] }
  remove(id: T['id']): void { this.entries.delete(id) }
}

