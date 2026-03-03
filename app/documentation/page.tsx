import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function DocumentationPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background text-foreground px-4">
      <div className="text-center max-w-md">
        <div className="w-12 h-12 bg-accent rounded-xl flex items-center justify-center mx-auto mb-6">
          <span className="text-accent-foreground font-bold text-lg">S</span>
        </div>
        <h1 className="text-4xl font-bold mb-4">Documentation</h1>
        <p className="text-muted-foreground text-lg mb-8">
          Full API reference and integration guides are coming soon.
        </p>
        <div className="flex gap-4 justify-center">
          <Button asChild>
            <Link href="/dashboard">Go to Dashboard</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/">Back to Home</Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
