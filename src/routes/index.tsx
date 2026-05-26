import { createFileRoute, Link } from "@tanstack/react-router";
import { Nav, Blobs } from "@/components/Nav";
import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles, Calculator, MessageCircle, CalendarDays } from "lucide-react";
import hero from "@/assets/hero-food.jpg";
import bowl from "@/assets/bowl.jpg";
import citrus from "@/assets/citrus.jpg";
import plate from "@/assets/plate.jpg";

export const Route = createFileRoute("/")({
  component: Index,
  head: () => ({
    meta: [
      { title: "NutriBot — Your AI-powered nutrition companion" },
      { name: "description", content: "Chat with NutriBot to track nutrition, calculate BMI, and generate accurate, AI-curated meal plans." },
    ],
  }),
});

function Index() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs />
      <Nav />
      <main className="relative z-10 mx-auto max-w-6xl px-4 pt-12 pb-24">
        {/* Hero */}
        <section className="grid lg:grid-cols-2 gap-10 items-center">
          <div>
            <div className="inline-flex items-center gap-2 glass rounded-full px-3 py-1 text-xs font-medium">
              <Sparkles className="h-3.5 w-3.5 text-citrus" />
              AI nutrition, made delicious
            </div>
            <h1 className="mt-5 text-5xl md:text-6xl font-display font-semibold leading-[1.05]">
              Eat smarter. <br />
              <span className="text-primary">Powered by AI.</span>
            </h1>
            <p className="mt-5 text-lg text-muted-foreground max-w-md">
              NutriBot blends a real food database with conversational AI to answer your nutrition questions and build meal plans that actually add up.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild size="lg" className="rounded-full">
                <Link to="/chat">Start chatting <ArrowRight className="ml-1 h-4 w-4" /></Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="rounded-full bg-white/60 backdrop-blur">
                <Link to="/bmi">Calculate BMI</Link>
              </Button>
            </div>
          </div>
          <div className="relative">
            <div className="glass rounded-3xl p-3 rotate-1">
              <img src={hero} alt="Fresh fruits and vegetables flat lay" width={1536} height={1024} className="rounded-2xl w-full h-auto" />
            </div>
            <div className="absolute -bottom-6 -left-6 glass rounded-2xl p-4 w-44 -rotate-3 hidden md:block">
              <div className="text-xs text-muted-foreground">Today</div>
              <div className="font-display text-2xl font-semibold">1,840 kcal</div>
              <div className="text-xs text-primary mt-1">On target ✓</div>
            </div>
            <div className="absolute -top-4 -right-4 glass rounded-2xl px-4 py-3 hidden md:block">
              <div className="text-xs text-muted-foreground">Protein</div>
              <div className="font-display text-xl font-semibold text-citrus">112g</div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="mt-24">
          <h2 className="text-3xl md:text-4xl font-display font-semibold text-center">Everything you need on your plate</h2>
          <p className="text-center text-muted-foreground mt-3 max-w-xl mx-auto">Four tools that work together, so the math is always right and the advice always tastes good.</p>
          <div className="mt-10 grid md:grid-cols-2 lg:grid-cols-4 gap-5">
            <FeatureCard icon={MessageCircle} title="RAG Chatbot" desc="Ask anything about food. Answers grounded in a real nutrition database." img={citrus} />
            <FeatureCard icon={Calculator} title="BMI & TDEE" desc="Get your numbers in seconds. Saved to your profile." img={bowl} />
            <FeatureCard icon={Sparkles} title="Meal Planner" desc="AI picks the foods, Python guarantees the macros add up." img={plate} />
            <FeatureCard icon={CalendarDays} title="Dashboard" desc="See your week at a glance with charts and a meal calendar." img={hero} />
          </div>
        </section>
      </main>
      <footer className="relative z-10 text-center text-xs text-muted-foreground py-8">
        NutriBot
      </footer>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, desc, img }: { icon: any; title: string; desc: string; img: string }) {
  return (
    <div className="glass rounded-3xl overflow-hidden flex flex-col group hover:-translate-y-1 transition-transform">
      <div className="aspect-[4/3] overflow-hidden">
        <img src={img} alt={title} loading="lazy" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
      </div>
      <div className="p-5">
        <div className="flex items-center gap-2">
          <span className="grid place-items-center h-8 w-8 rounded-full bg-primary/10 text-primary">
            <Icon className="h-4 w-4" />
          </span>
          <h3 className="font-display text-lg font-semibold">{title}</h3>
        </div>
        <p className="mt-2 text-sm text-muted-foreground">{desc}</p>
      </div>
    </div>
  );
}
