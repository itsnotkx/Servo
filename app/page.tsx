import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { ArrowRight, Zap, DollarSign, Layers } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">

      {/* Navbar */}
      <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-accent rounded-lg flex items-center justify-center">
              <span className="text-accent-foreground font-bold text-xs">S</span>
            </div>
            <span className="font-bold text-lg">Servo</span>
          </div>
          <nav className="hidden md:flex items-center gap-8 text-sm text-muted-foreground">
            <a href="#features" className="hover:text-foreground transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-foreground transition-colors">How It Works</a>
            <Link href="/documentation" className="hover:text-foreground transition-colors">Documentation</Link>
          </nav>
          <div className="flex items-center gap-3">
            <Button variant="ghost" asChild>
              <Link href="/sign-in">Sign In</Link>
            </Button>
            <Button asChild>
              <Link href="/sign-up">Get Started</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 py-28 text-center">
        <div className="inline-flex items-center gap-2 bg-accent/10 text-accent border border-accent/20 rounded-full px-4 py-1.5 text-sm font-medium mb-8">
          <Zap className="w-3.5 h-3.5" />
          Intelligent LLM Routing
        </div>
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 leading-tight">
          Route every request to<br />
          <span className="text-accent">the right model</span>
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
          Servo automatically classifies your prompts and routes them to the optimal model — cutting inference costs without sacrificing quality.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button size="lg" className="gap-2 text-base px-8" asChild>
            <Link href="/sign-up">
              Get Started Free
              <ArrowRight className="w-4 h-4" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" className="text-base px-8 bg-transparent" asChild>
            <Link href="/documentation">View Docs</Link>
          </Button>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-6xl mx-auto px-6 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Everything you need to optimize LLM costs</h2>
          <p className="text-muted-foreground text-lg max-w-xl mx-auto">Stop overpaying for simple requests. Servo routes intelligently so you only use expensive models when you actually need them.</p>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          <Card className="bg-card border-border p-8">
            <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center mb-5">
              <Zap className="w-5 h-5 text-accent" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Intelligent Routing</h3>
            <p className="text-muted-foreground leading-relaxed">
              Automatically classify request complexity and route each prompt to the most appropriate model tier in milliseconds.
            </p>
          </Card>
          <Card className="bg-card border-border p-8">
            <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center mb-5">
              <DollarSign className="w-5 h-5 text-accent" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Cost Optimization</h3>
            <p className="text-muted-foreground leading-relaxed">
              Route simple requests to lightweight models and save up to 80% on inference costs — with full visibility into spend per key.
            </p>
          </Card>
          <Card className="bg-card border-border p-8">
            <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center mb-5">
              <Layers className="w-5 h-5 text-accent" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Provider Flexibility</h3>
            <p className="text-muted-foreground leading-relaxed">
              Built on Google AI Studio today, with a provider-agnostic architecture ready to support any LLM provider you need tomorrow.
            </p>
          </Card>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="border-y border-border bg-card/30">
        <div className="max-w-6xl mx-auto px-6 py-24">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">How it works</h2>
            <p className="text-muted-foreground text-lg">Three steps. Zero configuration required.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: 'Send your request',
                description: 'Point your application at the Servo API endpoint. No changes to your existing prompts needed.',
              },
              {
                step: '02',
                title: 'Servo classifies complexity',
                description: 'Our classifier analyses your prompt and scores it against your configured routing rules in real time.',
              },
              {
                step: '03',
                title: 'The right model responds',
                description: 'Simple requests go to fast, cheap models. Complex ones go to powerful models. You pay only for what the task actually needs.',
              },
            ].map(({ step, title, description }) => (
              <div key={step} className="flex flex-col items-start">
                <span className="text-5xl font-bold text-accent/20 mb-4">{step}</span>
                <h3 className="text-xl font-semibold mb-3">{title}</h3>
                <p className="text-muted-foreground leading-relaxed">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="max-w-6xl mx-auto px-6 py-24 text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">Start routing smarter today</h2>
        <p className="text-muted-foreground text-lg mb-8 max-w-lg mx-auto">
          Create a free account, generate an API key, and cut your LLM costs in minutes.
        </p>
        <Button size="lg" className="gap-2 text-base px-8" asChild>
          <Link href="/sign-up">
            Create Free Account
            <ArrowRight className="w-4 h-4" />
          </Link>
        </Button>
      </section>

      {/* Footer */}
      <footer className="border-t border-border">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-accent rounded-md flex items-center justify-center">
              <span className="text-accent-foreground font-bold text-xs">S</span>
            </div>
            <span className="font-semibold">Servo</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-muted-foreground">
            <Link href="/documentation" className="hover:text-foreground transition-colors">Documentation</Link>
            <Link href="/sign-in" className="hover:text-foreground transition-colors">Sign In</Link>
          </div>
        </div>
      </footer>

    </div>
  )
}
