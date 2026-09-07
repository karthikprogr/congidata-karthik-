import { createFileRoute } from "@tanstack/react-router";
import { Navbar } from "@/components/site/Navbar";
import { Hero } from "@/components/site/Hero";
import {
  ProblemSection, ExistingSolutionsSection, ResearchFoundationSection, ResearchGapSection,
  SolutionSection, ApplicationsSection, WhatClientsSection, FeaturesSection, HowItWorks,
  AgentsSection, ModulesSection, ArchitectureSection, TechStackSection, DashboardPreviewSection,
  ClientBenefitsSection, ComparisonSection, FutureScopeSection, AboutSection, FaqSection,
  ContactSection, Footer,
} from "@/components/site/Sections";

export const Route = createFileRoute("/")({
  component: Index,
  head: () => ({
    meta: [
      { title: "CogniData — Multi-Agent AI Business Analytics Platform" },
      { name: "description", content: "CogniData turns business data into intelligent decisions using Multi-Agent AI, forecasting, natural language queries and executive-ready reports." },
      { property: "og:title", content: "CogniData — Multi-Agent AI Business Analytics Platform" },
      { property: "og:description", content: "Multi-Agent AI for business: validate, clean, analyze, forecast, recommend and report — one intelligent platform." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
});

function Index() {
  return (
    <div className="relative min-h-screen overflow-x-clip">
      <Navbar />
      <main>
        <Hero />
        <ProblemSection />
        <ExistingSolutionsSection />
        <ResearchFoundationSection />
        <ResearchGapSection />
        <SolutionSection />
        <ApplicationsSection />
        <WhatClientsSection />
        <FeaturesSection />
        <HowItWorks />
        <AgentsSection />
        <ModulesSection />
        <ArchitectureSection />
        <TechStackSection />
        <DashboardPreviewSection />
        <ClientBenefitsSection />
        <ComparisonSection />
        <FutureScopeSection />
        <AboutSection />
        <FaqSection />
        <ContactSection />
      </main>
      <Footer />
    </div>
  );
}
