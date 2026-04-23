import { HeroSection } from '@/components/landing/HeroSection';
import { ProblemStatement } from '@/components/landing/ProblemStatement';
import { StatsSection } from '@/components/landing/StatsSection';
import { HowItWorks } from '@/components/landing/HowItWorks';
import { FeatureSection } from '@/components/landing/FeatureSection';
import { CTASection } from '@/components/landing/CTASection';

export default function HomePage() {
  return (
    <>
      <HeroSection />
      <ProblemStatement />
      <StatsSection />
      <HowItWorks />
      <FeatureSection />
      <CTASection />
    </>
  );
}
