// TODO: load effective permissions from backend when permission endpoint is available
export function usePermission() {
  function can(_permission: string): boolean {
    return true
  }

  return { can }
}
