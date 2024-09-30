import { generateResponse } from '../../lib/rag'

export const runtime = 'edge'

export async function POST(req: Request) {
  const { messages } = await req.json()
  const lastMessage = messages[messages.length - 1]
  
  if (lastMessage.role !== 'user') {
    return new Response('Invalid request', { status: 400 })
  }

  const response = generateResponse(lastMessage.content)

  return new Response(JSON.stringify({ role: 'assistant', content: response }), {
    headers: { 'Content-Type': 'application/json' },
  })
}
