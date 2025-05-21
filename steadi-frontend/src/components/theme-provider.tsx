import { createContext, useContext, useEffect, useState } from "react"
import type { ReactNode } from "react"
import { ThemeProvider as NextThemesProvider } from "next-themes"

type ThemeProviderProps = {
  children: ReactNode;
  defaultTheme?: string;
  storageKey?: string;
}

const ThemeContext = createContext({ theme: "dark", setTheme: (_: string) => {} })

export function useTheme() {
  return useContext(ThemeContext)
}

export function ThemeProvider({ 
  children,
  defaultTheme = "dark",
  storageKey = "theme",
  ...props
}: ThemeProviderProps) {
  const [theme, setTheme] = useState(defaultTheme)

  useEffect(() => {
    // Get theme from localStorage or default to dark
    const savedTheme = localStorage.getItem(storageKey) || defaultTheme
    setTheme(savedTheme)
  }, [defaultTheme, storageKey])

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      <NextThemesProvider attribute="class" defaultTheme={defaultTheme} enableSystem={false} {...props}>
        {children}
      </NextThemesProvider>
    </ThemeContext.Provider>
  )
} 