import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import Link from 'next/link'
import Chat from './components/Chat'
import { createSupabaseClient } from './lib/supabase'

export const dynamic = 'force-dynamic'

export default async function Home() {
  const supabase = createServerComponentClient({ cookies })

  const {
    data: { session },
  } = await supabase.auth.getSession()

  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-2">
      <main className="flex flex-col items-center justify-center w-full flex-1 px-20 text-center">
        <h1 className="text-6xl font-bold mb-8">
          Welcome to the AI Chat App
        </h1>
        
        {!session ? (
          <div>
            <Link href="/login" className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
              Login
            </Link>
            <Link href="/signup" className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded ml-4">
              Sign Up
            </Link>
          </div>
        ) : (
          <div>
            <p className="mb-4">Welcome, {session.user.email}</p>
            <Chat />
            <form action="/auth/signout" method="post">
              <button className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded mt-4" type="submit">
                Sign out
              </button>
            </form>
          </div>
        )}
      </main>
    </div>
  )
}
