"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, Users, Wifi, Activity, Plus, Trash2, Settings } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"

// Configuração para desenvolvimento local e containers
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"

console.log("API URL:", API_BASE_URL) // Debug para verificar a URL da API

interface User {
  id: string
  name: string
  profile: string
  disabled: string
  daily_usage_mb: number
  limit_reached: boolean
}

interface DashboardStats {
  online_users: number
  total_users: number
  total_today_gb: number
  online_users_list: any[]
}

// Função helper para fazer requisições com fallback para proxy
async function apiRequest(endpoint: string, options: RequestInit = {}) {
  // Remover /api do início se existir para evitar duplicação
  const cleanEndpoint = endpoint.startsWith("/api") ? endpoint.substring(4) : endpoint

  const urls = [
    `${API_BASE_URL}/api${cleanEndpoint}`, // Tentar diretamente primeiro
    `/api/proxy${cleanEndpoint}`, // Fallback para proxy interno
  ]

  for (const url of urls) {
    try {
      console.log(`Tentando requisição para: ${url}`)
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      })

      if (response.ok) {
        console.log(`Sucesso na requisição para: ${url}`)
        return response
      } else {
        console.log(`Erro ${response.status} na requisição para: ${url}`)
      }
    } catch (error) {
      console.log(`Erro de rede para ${url}:`, error)
    }
  }

  throw new Error(`Falha em todas as tentativas de conexão para ${endpoint}`)
}

export default function HotspotManager() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [username, setUsername] = useState("admin") // Valor padrão para dev
  const [password, setPassword] = useState("admin") // Valor padrão para dev
  const [loginError, setLoginError] = useState("")
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [users, setUsers] = useState<User[]>([])
  const [profiles, setProfiles] = useState<string[]>([])
  const [newUser, setNewUser] = useState({ username: "", password: "", profile: "" })
  const [loading, setLoading] = useState(false)
  const [apiStatus, setApiStatus] = useState<"online" | "offline" | "checking">("checking")

  // Verificar status da API
  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        console.log("Verificando status da API...")
        const response = await apiRequest("/health")
        const data = await response.json()
        console.log("API respondeu:", data)
        setApiStatus("online")
      } catch (error) {
        console.error("Erro ao verificar API:", error)
        setApiStatus("offline")
      }
    }

    checkApiStatus()
    const interval = setInterval(checkApiStatus, 30000) // Verificar a cada 30s
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (isAuthenticated) {
      fetchStats()
      fetchUsers()
      fetchProfiles()

      // Atualizar dados a cada 30 segundos
      const interval = setInterval(() => {
        fetchStats()
        fetchUsers()
      }, 30000)

      return () => clearInterval(interval)
    }
  }, [isAuthenticated])

  const fetchStats = async () => {
    try {
      console.log("Buscando estatísticas...")
      const response = await apiRequest("/dashboard/stats")
      const data = await response.json()
      console.log("Estatísticas recebidas:", data)
      setStats(data)
    } catch (error) {
      console.error("Erro ao buscar estatísticas:", error)
    }
  }

  const fetchUsers = async () => {
    try {
      console.log("Buscando usuários...")
      const response = await apiRequest("/users")
      const data = await response.json()
      console.log("Usuários recebidos:", data)
      setUsers(data)
    } catch (error) {
      console.error("Erro ao buscar usuários:", error)
    }
  }

  const fetchProfiles = async () => {
    try {
      console.log("Buscando perfis...")
      const response = await apiRequest("/profiles")
      const data = await response.json()
      console.log("Perfis recebidos:", data)
      setProfiles(data)
    } catch (error) {
      console.error("Erro ao buscar perfis:", error)
    }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setLoginError("")

    try {
      console.log("Enviando login...")
      const response = await apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      })

      const data = await response.json()
      console.log("Resposta do login:", data)

      if (response.ok && data.success) {
        setIsAuthenticated(true)
      } else {
        setLoginError(data.message || "Erro ao fazer login")
      }
    } catch (error) {
      console.error("Erro de conexão:", error)
      setLoginError(`Erro de conexão com o servidor. Verifique se a API está rodando.`)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      console.log("Criando usuário...")
      const response = await apiRequest("/users", {
        method: "POST",
        body: JSON.stringify(newUser),
      })

      if (response.ok) {
        const data = await response.json()
        console.log("Usuário criado:", data)
        setNewUser({ username: "", password: "", profile: "" })
        fetchUsers()
      } else {
        console.error("Erro ao criar usuário:", response.status)
      }
    } catch (error) {
      console.error("Erro ao criar usuário:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteUser = async (username: string) => {
    if (!confirm(`Tem certeza que deseja excluir o usuário ${username}?`)) {
      return
    }

    try {
      console.log("Excluindo usuário:", username)
      const response = await apiRequest(`/users/${username}`, {
        method: "DELETE",
      })

      if (response.ok) {
        const data = await response.json()
        console.log("Usuário excluído:", data)
        fetchUsers()
      } else {
        console.error("Erro ao excluir usuário:", response.status)
      }
    } catch (error) {
      console.error("Erro ao excluir usuário:", error)
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-center">Hotspot Manager</CardTitle>
            <CardDescription className="text-center">Sistema de gerenciamento MikroTik</CardDescription>

            {/* Status da API */}
            <div className="flex items-center justify-center space-x-2 mt-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  apiStatus === "online" ? "bg-green-500" : apiStatus === "offline" ? "bg-red-500" : "bg-yellow-500"
                }`}
              ></div>
              <span className="text-xs text-gray-500">
                API: {apiStatus === "online" ? "Online" : apiStatus === "offline" ? "Offline" : "Verificando..."}
              </span>
            </div>
            <div className="text-xs text-gray-400 text-center">Conectando em: {API_BASE_URL}</div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Usuário</Label>
                <Input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Senha</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              {loginError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{loginError}</AlertDescription>
                </Alert>
              )}
              <Button type="submit" className="w-full" disabled={loading || apiStatus === "offline"}>
                {loading ? "Entrando..." : "Entrar"}
              </Button>

              {/* Informações de desenvolvimento */}
              <div className="text-xs text-gray-500 text-center space-y-1">
                <div>💡 Modo Desenvolvimento</div>
                <div>Login padrão: admin / admin</div>
                <div>Certifique-se que a API Flask está rodando</div>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Hotspot Manager</h1>
              <p className="text-gray-600 mt-2">Sistema de gerenciamento de hotspot MikroTik</p>
            </div>

            {/* Status da API no dashboard */}
            <div className="flex items-center space-x-2">
              <div
                className={`w-3 h-3 rounded-full ${
                  apiStatus === "online" ? "bg-green-500" : apiStatus === "offline" ? "bg-red-500" : "bg-yellow-500"
                }`}
              ></div>
              <span className="text-sm text-gray-600">
                API {apiStatus === "online" ? "Online" : apiStatus === "offline" ? "Offline" : "Verificando..."}
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Usuários Online</CardTitle>
              <Wifi className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.online_users || 0}</div>
              <p className="text-xs text-muted-foreground">Conectados agora</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total de Usuários</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_users || 0}</div>
              <p className="text-xs text-muted-foreground">Cadastrados</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Consumo Hoje</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_today_gb || 0} GB</div>
              <p className="text-xs text-muted-foreground">Total transferido</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Sistema</CardTitle>
              <Settings className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">Online</div>
              <p className="text-xs text-muted-foreground">Status do sistema</p>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="users" className="space-y-4">
          <TabsList>
            <TabsTrigger value="users">Gerenciar Usuários</TabsTrigger>
            <TabsTrigger value="create">Criar Usuário</TabsTrigger>
          </TabsList>

          <TabsContent value="users" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Usuários do Hotspot</CardTitle>
                <CardDescription>Lista de todos os usuários cadastrados no sistema</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {users.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      Nenhum usuário encontrado. Crie o primeiro usuário na aba "Criar Usuário".
                    </div>
                  ) : (
                    users.map((user) => (
                      <div key={user.id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex items-center space-x-4">
                          <div>
                            <h3 className="font-medium">{user.name}</h3>
                            <p className="text-sm text-gray-500">Perfil: {user.profile}</p>
                            <p className="text-sm text-gray-500">Consumo hoje: {user.daily_usage_mb} MB</p>
                          </div>
                          <div className="flex space-x-2">
                            {user.disabled === "true" && <Badge variant="secondary">Desabilitado</Badge>}
                            {user.limit_reached && <Badge variant="destructive">Limite Atingido</Badge>}
                          </div>
                        </div>
                        <Button variant="destructive" size="sm" onClick={() => handleDeleteUser(user.name)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="create" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Criar Novo Usuário</CardTitle>
                <CardDescription>Adicione um novo usuário ao sistema de hotspot</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleCreateUser} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="new-username">Nome de Usuário</Label>
                      <Input
                        id="new-username"
                        value={newUser.username}
                        onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="new-password">Senha</Label>
                      <Input
                        id="new-password"
                        type="password"
                        value={newUser.password}
                        onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="new-profile">Perfil</Label>
                    <select
                      id="new-profile"
                      className="w-full p-2 border rounded-md"
                      value={newUser.profile}
                      onChange={(e) => setNewUser({ ...newUser, profile: e.target.value })}
                      required
                    >
                      <option value="">Selecione um perfil</option>
                      {profiles.map((profile) => (
                        <option key={profile} value={profile}>
                          {profile}
                        </option>
                      ))}
                    </select>
                  </div>
                  <Button type="submit" disabled={loading}>
                    <Plus className="h-4 w-4 mr-2" />
                    {loading ? "Criando..." : "Criar Usuário"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
