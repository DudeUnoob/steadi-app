"use client"

import { useRef } from "react"
import { useInView } from "framer-motion"
import { BarChart3, Users, Package, TrendingUp, Shield, Zap, LineChart, PieChart, BarChart } from "lucide-react"

export function LandingFeatures() {
    const ref = useRef(null)
    const isInView = useInView(ref, { once: true, amount: 0.2 })

    const features = [
        {
            icon: <BarChart3 className="h-10 w-10 text-steadi-red" />,
            title: "Advanced Analytics",
            description: "Gain deep insights into your business performance with AI-powered analytics and visualizations.",
        },
        {
            icon: <Users className="h-10 w-10 text-steadi-pink" />,
            title: "Supplier Management",
            description: "Streamline your supplier relationships and optimize your supply chain with intelligent tracking.",
        },
        {
            icon: <Package className="h-10 w-10 text-steadi-purple" />,
            title: "Product Inventory",
            description: "Keep track of your inventory in real-time and receive smart restocking recommendations.",
        },
        {
            icon: <TrendingUp className="h-10 w-10 text-steadi-red" />,
            title: "Sales Forecasting",
            description: "Predict future sales trends with machine learning models trained on your historical data.",
        },
        {
            icon: <Shield className="h-10 w-10 text-steadi-pink" />,
            title: "Role-Based Access",
            description: "Control who can view and edit your business data with granular permission settings.",
        },
        {
            icon: <Zap className="h-10 w-10 text-steadi-purple" />,
            title: "Real-Time Updates",
            description: "Stay informed with instant notifications and real-time dashboard updates.",
        },
    ]

    return (
        <section id="features" className="py-20 relative overflow-hidden" ref={ref}>
            <div className="container px-4 md:px-6">
                <div className="text-center space-y-4 mb-16">
                    <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
                        Powerful Features for Your Business
                    </h2>
                    <p className="mx-auto max-w-[700px] text-muted-foreground md:text-xl">
                        Steadi combines cutting-edge AI with intuitive design to help you manage your business more efficiently.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {features.map((feature, index) => (
                        <div
                            key={index}
                            className={`rounded-xl border border-[#2a2a30] bg-black/40 backdrop-blur-md p-6 transition-all duration-700 ease-out ${isInView ? "translate-y-0 opacity-100" : "translate-y-10 opacity-0"
                                }`}
                            style={{ transitionDelay: `${150 * index}ms` }}
                        >
                            <div className="mb-4 rounded-full w-16 h-16 flex items-center justify-center bg-muted/20">
                                {feature.icon}
                            </div>
                            <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                            <p className="text-muted-foreground">{feature.description}</p>
                        </div>
                    ))}
                </div>

                <div
                    className={`mt-20 rounded-xl border border-[#2a2a30] bg-black/40 backdrop-blur-md overflow-hidden transition-all duration-700 ease-out ${isInView ? "translate-y-0 opacity-100" : "translate-y-10 opacity-0"
                        }`}
                    style={{ transitionDelay: "600ms" }}
                >
                    <div className="grid md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-[#2a2a30]">
                        <div className="p-8 text-center">
                            <div className="flex justify-center mb-4">
                                <BarChart className="h-10 w-10 text-steadi-red" />
                            </div>
                            <h3 className="text-2xl font-bold mb-2">500+</h3>
                            <p className="text-muted-foreground">Businesses Powered</p>
                        </div>
                        <div className="p-8 text-center">
                            <div className="flex justify-center mb-4">
                                <LineChart className="h-10 w-10 text-steadi-pink" />
                            </div>
                            <h3 className="text-2xl font-bold mb-2">30%</h3>
                            <p className="text-muted-foreground">Average Growth</p>
                        </div>
                        <div className="p-8 text-center">
                            <div className="flex justify-center mb-4">
                                <PieChart className="h-10 w-10 text-steadi-purple" />
                            </div>
                            <h3 className="text-2xl font-bold mb-2">24/7</h3>
                            <p className="text-muted-foreground">AI-Powered Support</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    )
}
