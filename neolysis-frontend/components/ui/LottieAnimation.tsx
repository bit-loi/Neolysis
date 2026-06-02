'use client';
/* eslint-disable @typescript-eslint/no-explicit-any */

import dynamic from 'next/dynamic';

const Lottie = dynamic(() => import('lottie-react'), { 
  ssr: false,
  loading: () => <div className="w-8 h-8 border-2 border-gray-200 border-t-black rounded-full animate-spin"></div> 
});

interface LottieAnimationProps {
  animationData: any;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  loop?: boolean;
}

export function LottieAnimation({ animationData, size = 'md', loop = true }: LottieAnimationProps) {
  const sizeClasses = {
    sm: 'w-16 h-16',
    md: 'w-32 h-32',
    lg: 'w-48 h-48',
    xl: 'w-64 h-64'
  };

  return (
    <div className="flex items-center justify-center">
      <div className={`${sizeClasses[size]} flex items-center justify-center`}>
        <Lottie 
          animationData={animationData} 
          loop={loop} 
          autoplay={true}
        />
      </div>
    </div>
  );
}
