import type { Contact, ContactStatus } from '~/types/contacts'

/** Badge color per contact status (Nuxt UI v4 semantic color aliases). */
export function contactStatusColor(status: ContactStatus) {
  return ({
    lead: 'neutral',
    qualified: 'info',
    customer: 'success',
    churned: 'error',
  } as const)[status] ?? 'neutral'
}

export function contactFullName(contact: Contact): string {
  return [contact.first_name, contact.last_name].filter(Boolean).join(' ')
}
