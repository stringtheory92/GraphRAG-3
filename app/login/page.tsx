'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()
  const supabase = createClientComponentClient()

  const handleSignIn = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })
      if (error) throw error
      router.push('/')
      router.refresh()
    } catch (error) {
      console.error('Error during sign in:', error)
      setError('Failed to sign in. Please check your credentials and try again.')
    }
  }

  const handleTestLogin = async () => {
    setError(null)
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email: 'test@example.com',
        password: 'testpassword123',
      })
      if (error) throw error
      router.push('/')
      router.refresh()
    } catch (error) {
      console.error('Error during test login:', error)
      setError('Failed to sign in with test account. Please try again.')
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-2">
      <form onSubmit={handleSignIn} className="flex flex-col space-y-4">
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="px-4 py-2 border rounded-md"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="px-4 py-2 border rounded-md"
        />
        <button type="submit" className="px-4 py-2 bg-blue-500 text-white rounded-md">
          Sign In
        </button>
      </form>
      <button 
        onClick={handleTestLogin} 
        className="mt-4 px-4 py-2 bg-green-500 text-white rounded-md"
      >
        Use Test Account
      </button>
      {error && <p className="text-red-500 mt-4">{error}</p>}
    </div>
  )
}
