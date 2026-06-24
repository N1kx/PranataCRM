export type SuiteRole = 'tenant_owner' | 'tenant_admin' | 'member'

export interface AuthUser {
  id: string
  email: string
  full_name: string
  suite_role: SuiteRole
}

export interface RegisterTenantPayload {
  full_name: string
  email: string
  password: string
  organization_name: string
  slug: string
  industry?: string
  team_size?: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface AcceptInvitePayload {
  token: string
  full_name: string
  password: string
}

export interface CreateUserPayload {
  full_name: string
  email: string
  password: string
  role_id: string
}

export interface InviteUserPayload {
  email: string
  full_name?: string
  role_id: string
}

export interface ApiError {
  error: {
    code: string
    message: string
    detail: string | null
  }
}
