export interface GeoCountry {
  code: string
  name_en: string
  name_id?: string | null
  is_active: boolean
}

export interface GeoState {
  id: string
  country_code: string
  name: string
  code?: string | null
  is_active: boolean
}

export interface GeoCity {
  id: string
  state_id: string
  country_code: string
  name: string
  is_active: boolean
}

/** Flattened {label, value} shape consumed by USelectMenu everywhere in the UI. */
export interface GeoOption {
  label: string
  value: string
}

export interface GeoStateCreatePayload {
  country_code: string
  name: string
  code?: string | null
}

export interface GeoStateUpdatePayload {
  name?: string
  code?: string | null
  is_active?: boolean
}

export interface GeoCityCreatePayload {
  state_id: string
  name: string
}

export interface GeoCityUpdatePayload {
  name?: string
  is_active?: boolean
}
