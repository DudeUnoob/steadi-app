import { useEffect, useRef, useState } from 'react';
import { prefetchDashboardData } from '@/lib/api';

interface PerformanceMetrics {
  renderTime: number;
  apiResponseTime: number;
  memoryUsage?: number;
}

export function usePerformanceMonitor(componentName: string) {
  const renderStartTime = useRef<number>(Date.now());
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);

  useEffect(() => {
    const renderTime = Date.now() - renderStartTime.current;
    
    // Log render performance
    if (renderTime > 100) { // Log if render takes more than 100ms
      console.warn(`${componentName} render time: ${renderTime}ms`);
    }

    // Get memory usage if available
    const memoryUsage = (performance as any).memory?.usedJSHeapSize;
    
    setMetrics({
      renderTime,
      apiResponseTime: 0, // Will be updated by API calls
      memoryUsage
    });

    // Clean up large objects on unmount
    return () => {
      // Trigger garbage collection hint if available
      if ('gc' in window && typeof (window as any).gc === 'function') {
        (window as any).gc();
      }
    };
  }, [componentName]);

  return metrics;
}

export function useIntersectionObserver(
  elementRef: React.RefObject<Element>,
  options: IntersectionObserverInit = {}
) {
  const [isIntersecting, setIsIntersecting] = useState(false);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting);
        
        // Prefetch data when component comes into view
        if (entry.isIntersecting) {
          prefetchDashboardData();
        }
      },
      {
        threshold: 0.1,
        ...options,
      }
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [elementRef, options]);

  return isIntersecting;
}

// Debounce hook for search inputs
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Virtual scrolling hook for large lists
export function useVirtualScrolling(
  items: any[],
  itemHeight: number,
  containerHeight: number
) {
  const [scrollTop, setScrollTop] = useState(0);
  
  const startIndex = Math.floor(scrollTop / itemHeight);
  const endIndex = Math.min(
    startIndex + Math.ceil(containerHeight / itemHeight) + 1,
    items.length
  );
  
  const visibleItems = items.slice(startIndex, endIndex);
  
  const offsetY = startIndex * itemHeight;
  const totalHeight = items.length * itemHeight;
  
  return {
    visibleItems,
    offsetY,
    totalHeight,
    setScrollTop,
    startIndex,
    endIndex
  };
}

// Image lazy loading hook
export function useLazyImage(src: string) {
  const [imageSrc, setImageSrc] = useState<string>('');
  const [imageRef, setImageRef] = useState<HTMLImageElement | null>(null);

  useEffect(() => {
    let observer: IntersectionObserver;
    
    if (imageRef && imageSrc !== src) {
      observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              setImageSrc(src);
              observer.unobserve(imageRef);
            }
          });
        },
        { threshold: 0.1 }
      );
      
      observer.observe(imageRef);
    }
    
    return () => {
      if (observer && imageRef) {
        observer.unobserve(imageRef);
      }
    };
  }, [imageRef, src, imageSrc]);

  return [imageSrc, setImageRef] as const;
} 