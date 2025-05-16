"use client"

import { useRef, useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { motion, useScroll, useTransform } from "framer-motion"
import { Button } from "@/components/ui/button"
import { TrendingUp, BarChart3 } from "lucide-react"

export function LandingHero() {
    const ref = useRef(null)
    const [isVisible, setIsVisible] = useState(false)
    const { scrollYProgress } = useScroll({
        target: ref,
        offset: ["start start", "end start"],
    })

    useEffect(() => {
        setIsVisible(true)
    }, [])

    const backgroundY = useTransform(scrollYProgress, [0, 1], ["0%", "100%"])
    const textY = useTransform(scrollYProgress, [0, 1], ["0%", "200%"])

    return (
        <div
            ref={ref}
            className="relative min-h-screen flex items-center justify-center overflow-hidden"
            style={{
                background: "linear-gradient(to bottom, #000000, #1a0122)",
            }}
        >
            {/* Animated gradient background */}
            <motion.div
                className="absolute inset-0 z-0"
                style={{ y: backgroundY }}
            >
                <div className="absolute inset-0 bg-gradient-to-r from-steadi-red/20 via-steadi-pink/20 to-steadi-purple/20" />
                <div className="absolute top-[10%] -left-[10%] w-[500px] h-[500px] rounded-full bg-steadi-red/10 blur-[100px]" />
                <div className="absolute top-[40%] -right-[10%] w-[600px] h-[600px] rounded-full bg-steadi-purple/10 blur-[100px]" />
                <div className="absolute bottom-[10%] left-[20%] w-[300px] h-[300px] rounded-full bg-steadi-pink/10 blur-[100px]" />
            </motion.div>

            {/* Hero content */}
            <div className="container relative z-10 px-4 md:px-6 py-20">
                <div className="grid gap-12 md:grid-cols-2 md:gap-16 items-center">
                    <motion.div
                        className="text-left max-w-2xl"
                        style={{ y: textY }}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                    >
                        <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tighter mb-8">
                            Smart <span className="steadi-gradient-text">Business Intelligence</span>
                            <br />
                            for Small Businesses
                        </h1>

                        <p className="text-base md:text-xl text-muted-foreground mb-12">
                            Steadi helps small businesses optimize their operations, 
                            manage suppliers efficiently, and make data-driven decisions
                            with AI-powered analytics.
                        </p>

                        <div className="flex flex-col sm:flex-row gap-4">
                            <Link to="/auth">
                                <Button size="lg" className="bg-gradient-to-r from-steadi-red via-steadi-pink to-steadi-purple hover:opacity-90">
                                    Get Started Free
                                </Button>
                            </Link>
                            <Button variant="outline" size="lg" className="border-[#2a2a30] bg-transparent">
                                Watch Demo
                            </Button>
                        </div>

                        <div className="mt-16 pt-8 border-t border-[#2a2a30] flex flex-wrap gap-8">
                            <div className="flex items-center">
                                <div className="text-3xl font-bold steadi-gradient-text mr-3">2,500+</div>
                                <div className="text-sm text-muted-foreground text-left">Active Users</div>
                            </div>
                            <div className="flex items-center">
                                <div className="text-3xl font-bold steadi-gradient-text mr-3">75%</div>
                                <div className="text-sm text-muted-foreground text-left">Cost Reduction</div>
                            </div>
                            <div className="flex items-center">
                                <div className="text-3xl font-bold steadi-gradient-text mr-3">24/7</div>
                                <div className="text-sm text-muted-foreground text-left">Support</div>
                            </div>
                        </div>
                    </motion.div>

                    {/* Dashboard Preview */}
                    <div
                        className={`relative transition-all duration-700 delay-300 ${
                        isVisible ? "translate-y-0 opacity-100" : "translate-y-10 opacity-0"
                        }`}
                    >
                        <div className="relative mx-auto aspect-video overflow-hidden rounded-xl border border-[#2a2a30] bg-black/40 backdrop-blur-md shadow-2xl">
                        <div className="absolute inset-0 bg-gradient-to-br from-steadi-red/5 via-steadi-pink/5 to-steadi-purple/5"></div>
                        <div className="relative p-4 md:p-8 h-full flex flex-col">
                            <div className="flex items-center justify-between mb-6">
                            <div className="text-lg font-semibold">Dashboard Overview</div>
                            <div className="flex space-x-2">
                                <div className="h-3 w-3 rounded-full bg-steadi-red"></div>
                                <div className="h-3 w-3 rounded-full bg-steadi-pink"></div>
                                <div className="h-3 w-3 rounded-full bg-steadi-purple"></div>
                            </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4 mb-6">
                            <div className="rounded-lg bg-black/30 p-4 border border-[#2a2a30]">
                                <div className="flex items-center justify-between">
                                <div className="text-sm text-muted-foreground">Revenue</div>
                                <TrendingUp className="h-4 w-4 text-green-500" />
                                </div>
                                <div className="mt-2 text-2xl font-bold">$45,231</div>
                                <div className="mt-1 text-xs text-green-500">+12.5% from last month</div>
                            </div>
                            <div className="rounded-lg bg-black/30 p-4 border border-[#2a2a30]">
                                <div className="flex items-center justify-between">
                                <div className="text-sm text-muted-foreground">Suppliers</div>
                                <BarChart3 className="h-4 w-4 text-steadi-pink" />
                                </div>
                                <div className="mt-2 text-2xl font-bold">24</div>
                                <div className="mt-1 text-xs text-steadi-pink">+3 new this month</div>
                            </div>
                            </div>
                            <div className="flex-1 rounded-lg bg-black/30 p-4 border border-[#2a2a30]">
                            <div className="flex items-center justify-between mb-4">
                                <div className="text-sm font-medium">Sales Overview</div>
                                <div className="text-xs text-muted-foreground">Last 6 months</div>
                            </div>
                            <div className="h-32 flex items-end justify-between px-2">
                                <div className="w-1/6 flex flex-col items-center">
                                <div
                                    className="w-full bg-gradient-to-t from-steadi-red to-steadi-pink rounded-t-sm"
                                    style={{ height: "40%" }}
                                ></div>
                                <div className="mt-2 text-xs text-muted-foreground">Jul</div>
                                </div>
                                <div className="w-1/6 flex flex-col items-center">
                                <div
                                    className="w-full bg-gradient-to-t from-steadi-red to-steadi-pink rounded-t-sm"
                                    style={{ height: "65%" }}
                                ></div>
                                <div className="mt-2 text-xs text-muted-foreground">Aug</div>
                                </div>
                                <div className="w-1/6 flex flex-col items-center">
                                <div
                                    className="w-full bg-gradient-to-t from-steadi-red to-steadi-pink rounded-t-sm"
                                    style={{ height: "50%" }}
                                ></div>
                                <div className="mt-2 text-xs text-muted-foreground">Sep</div>
                                </div>
                                <div className="w-1/6 flex flex-col items-center">
                                <div
                                    className="w-full bg-gradient-to-t from-steadi-red to-steadi-pink rounded-t-sm"
                                    style={{ height: "70%" }}
                                ></div>
                                <div className="mt-2 text-xs text-muted-foreground">Oct</div>
                                </div>
                                <div className="w-1/6 flex flex-col items-center">
                                <div
                                    className="w-full bg-gradient-to-t from-steadi-red to-steadi-pink rounded-t-sm"
                                    style={{ height: "60%" }}
                                ></div>
                                <div className="mt-2 text-xs text-muted-foreground">Nov</div>
                                </div>
                                <div className="w-1/6 flex flex-col items-center">
                                <div
                                    className="w-full bg-gradient-to-t from-steadi-red to-steadi-pink rounded-t-sm"
                                    style={{ height: "90%" }}
                                ></div>
                                <div className="mt-2 text-xs text-muted-foreground">Dec</div>
                                </div>
                            </div>
                            </div>
                        </div>
                        </div>
                        <div className="absolute -bottom-6 -right-6 h-64 w-64 rounded-full bg-steadi-purple/20 blur-3xl"></div>
                        <div className="absolute -top-6 -left-6 h-64 w-64 rounded-full bg-steadi-red/20 blur-3xl"></div>
                    </div>
                </div>
            </div>

            {/* Down arrow indicator */}
            <div className="absolute bottom-10 left-1/2 transform -translate-x-1/2 z-10 animate-bounce">
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="text-white/50"
                >
                    <path d="M12 5v14M5 12l7 7 7-7" />
                </svg>
            </div>
        </div>
    )
}
