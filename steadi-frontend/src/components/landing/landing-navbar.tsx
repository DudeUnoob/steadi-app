"use client"

import { useState } from "react"
import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Menu, X } from "lucide-react"

export function LandingNavbar() {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

    const toggleMobileMenu = () => {
        setIsMobileMenuOpen(!isMobileMenuOpen)
    }

    const closeMobileMenu = () => {
        setIsMobileMenuOpen(false)
    }

    return (
        <header className="sticky top-0 z-40 w-full border-b border-[#2a2a30] bg-black/60 backdrop-blur-xl">
            <div className="container flex h-16 items-center justify-between px-4 md:px-6">
                <div className="flex gap-6 md:gap-10">
                    <Link to="/" className="flex items-center space-x-2">
                        <div className="flex items-center">
                            <div className="h-8 w-8 bg-gradient-to-r from-steadi-red to-steadi-purple rounded-md"></div>
                            <span className="ml-2 text-2xl font-semibold">Steadi.</span>
                        </div>
                    </Link>
                    <nav className="hidden md:flex gap-6">
                        <a href="#features"
                            className="flex items-center text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                        >
                            Features
                        </a>
                        <a
                            href="#testimonials"
                            className="flex items-center text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                        >
                            Testimonials
                        </a>
                        <a
                            href="#pricing"
                            className="flex items-center text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                        >
                            Pricing
                        </a>
                    </nav>
                </div>
                <div className="hidden md:flex gap-4">
                    <Link to="/auth">
                        <Button variant="outline" className="border-[#2a2a30] bg-transparent">Login</Button>
                    </Link>
                    <Link to="/auth">
                        <Button className="bg-gradient-to-r from-steadi-red via-steadi-pink to-steadi-purple hover:opacity-90">Get Started</Button>
                    </Link>
                </div>
                <button
                    className="flex items-center justify-center rounded-md md:hidden p-2"
                    onClick={toggleMobileMenu}
                    aria-label="Toggle Menu"
                >
                    {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
                </button>
            </div>
            {isMobileMenuOpen && (
                <div className="md:hidden fixed inset-0 top-16 z-50 min-h-screen w-full bg-black/95 backdrop-blur-sm animate-in fade-in">
                    <div className="container px-4 py-8 flex flex-col gap-6">
                        <nav className="flex flex-col gap-4">
                            <a
                                href="#features"
                                className="text-base font-medium hover:text-steadi-pink"
                                onClick={closeMobileMenu}
                            >
                                Features
                            </a>
                            <a
                                href="#testimonials"
                                className="text-base font-medium hover:text-steadi-pink"
                                onClick={closeMobileMenu}
                            >
                                Testimonials
                            </a>
                            <a
                                href="#pricing"
                                className="text-base font-medium hover:text-steadi-pink"
                                onClick={closeMobileMenu}
                            >
                                Pricing
                            </a>
                        </nav>
                        <div className="flex flex-col gap-4 mt-4">
                            <Link to="/auth" onClick={() => setIsMobileMenuOpen(false)}>
                                <Button variant="outline" className="w-full border-[#2a2a30] bg-transparent">Login</Button>
                            </Link>
                            <Link to="/auth" onClick={() => setIsMobileMenuOpen(false)}>
                                <Button className="w-full bg-gradient-to-r from-steadi-red via-steadi-pink to-steadi-purple hover:opacity-90">Get Started</Button>
                            </Link>
                        </div>
                    </div>
                </div>
            )}
        </header>
    )
}
