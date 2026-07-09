import type { Contact, ContactStatus } from '~/types/contacts'

/** Badge color per contact status (Nuxt UI v2 palette). */
export function contactStatusColor(status: ContactStatus) {
  return ({
    lead: 'gray',
    qualified: 'blue',
    customer: 'green',
    churned: 'red',
  } as const)[status] ?? 'gray'
}

export function contactFullName(contact: Contact): string {
  return [contact.first_name, contact.last_name].filter(Boolean).join(' ')
}
