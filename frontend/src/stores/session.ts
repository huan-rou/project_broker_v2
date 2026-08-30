import { defineStore } from 'pinia'

export const useSessionStore = defineStore('session', {
  state: () => ({
    token: localStorage.getItem('demo_token') || '',
    displayName: localStorage.getItem('demo_display_name') || '',
    role: localStorage.getItem('demo_role') || ''
  }),
  actions: {
    setSession(token: string, displayName: string, role: string) {
      this.token = token
      this.displayName = displayName
      this.role = role
      localStorage.setItem('demo_token', token)
      localStorage.setItem('demo_display_name', displayName)
      localStorage.setItem('demo_role', role)
    },
    clear() {
      this.token = ''
      this.displayName = ''
      this.role = ''
      localStorage.clear()
    }
  }
})
