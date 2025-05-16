"use client"

import { useRef } from "react"
import { useInView } from "framer-motion"
import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { ArrowRight, CheckCircle } from "lucide-react"

export function LandingCta() {
    const ref = useRef(null)
    const isInView = useInView(ref, { once: true, amount: 0.2 })

    const benefits = [
        "AI-powered business intelligence",
        "Real-time analytics dashboard",
        "Supplier and inventory management",
        "Role-based access control",
        "Sales forecasting and reporting",
        "24/7 technical support",
    ]

    return (
        <section id="pricing" className="py-20 relative overflow-hidden" ref={ref}>
            <div className="container px-4 md:px-6">
                <div
                    className={`rounded-3xl border border-[#2a2a30] bg-black/40 backdrop-blur-md overflow-hidden transition-all duration-700 ease-out ${isInView ? "translate-y-0 opacity-100" : "translate-y-10 opacity-0"
                        }`}
                >
                    <div className="grid md:grid-cols-2">
                        <div className="p-8 md:p-12 lg:p-16 flex flex-col justify-center">
                            <div className="space-y-4">
                                <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Ready to transform your business?</h2>
                                <p className="text-muted-foreground md:text-lg">
                                    Start your 14-day free trial today. No credit card required.
                                </p>
                                <ul className="space-y-2 mt-6">
                                    {benefits.map((benefit, index) => (
                                        <li key={index} className="flex items-center">
                                            <CheckCircle className="h-5 w-5 text-steadi-pink mr-2" />
                                            <span>{benefit}</span>
                                        </li>
                                    ))}
                                </ul>
                                <div className="pt-6">
                                    <Link to="/auth">
                                        <Button size="lg" className="bg-steadi-pink hover:bg-steadi-pink/90">
                                            Get Started
                                            <ArrowRight className="ml-2 h-4 w-4" />
                                        </Button>
                                    </Link>
                                </div>
                            </div>
                        </div>
                        <div className="relative hidden md:block">
                            <div className="absolute inset-0 bg-gradient-to-br from-steadi-red/20 via-steadi-pink/20 to-steadi-purple/20"></div>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <div className="text-center space-y-4 p-8">
                                    <div className="text-5xl font-bold steadi-gradient-text">$49</div>
                                    <div className="text-xl font-medium">per month</div>
                                    <div className="text-sm text-muted-foreground">Billed annually or $59 monthly</div>
                                    <div className="pt-4">
                                        <Link to="/auth">
                                            <Button size="lg" variant="outline" className="border-white/20 bg-black/30 hover:bg-black/50">
                                                Start Free Trial
                                            </Button>
                                        </Link>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    )
}
