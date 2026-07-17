import type { Company, CompanyStatus, CompanyType } from '~/types/companies'

/** Badge color per company status (Nuxt UI v4 semantic color aliases). */
export function companyStatusColor(status: CompanyStatus) {
  return ({
    active: 'success',
    inactive: 'neutral',
  } as const)[status] ?? 'neutral'
}

/** Badge color per company type (Nuxt UI v4 semantic color aliases). */
export function companyTypeColor(type: CompanyType) {
  return ({
    prospect: 'info',
    customer: 'success',
    partner: 'primary',
    vendor: 'warning',
    competitor: 'error',
    other: 'neutral',
  } as const)[type] ?? 'neutral'
}

export function companyDisplayName(company: Company): string {
  return company.name
}
