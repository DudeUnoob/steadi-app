"use client"

import { useRef } from "react"
import { useInView } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Quote } from "lucide-react"

interface Testimonial {
    content: string
    author: {
        name: string
        role: string
        company: string
        avatar: string
    }
}

export function LandingTestimonials() {
    const ref = useRef(null)
    const isInView = useInView(ref, { once: true, amount: 0.2 })

    const testimonials: Testimonial[] = [
        {
            content:
                "Steadi has completely transformed how we manage our supply chain. The AI recommendations have saved us thousands in inventory costs.",
            author: {
                name: "Alex Morgan",
                role: "Operations Director",
                company: "TechGrowth Inc.",
                avatar: "/placeholder.svg?height=40&width=40",
            },
        },
        {
            content:
                "The analytics dashboard gives me instant insights into our business performance. I can make data-driven decisions faster than ever before.",
            author: {
                name: "Jamie Chen",
                role: "CEO",
                company: "Nimble Solutions",
                avatar: "/placeholder.svg?height=40&width=40",
            },
        },
        {
            content:
                "Setting up role-based permissions was a game-changer for our team. Everyone has exactly the access they need, no more, no less.",
            author: {
                name: "Sam Wilson",
                role: "IT Manager",
                company: "Quantum Retail",
                avatar: "/placeholder.svg?height=40&width=40",
            },
        },
    ]

    return (
        <section id="testimonials" className="py-20 relative overflow-hidden" ref={ref}>
            <div className="container px-4 md:px-6">
                <div className="text-center space-y-4 mb-16">
                    <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
                        Trusted by Businesses Everywhere
                    </h2>
                    <p className="mx-auto max-w-[700px] text-muted-foreground md:text-xl">
                        See what our customers have to say about how Steadi has transformed their operations.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {testimonials.map((testimonial, index) => (
                        <Card
                            key={index}
                            className={`border-[#2a2a30] bg-black/40 backdrop-blur-md transition-all duration-700 ease-out ${isInView ? "translate-y-0 opacity-100" : "translate-y-10 opacity-0"
                                }`}
                            style={{ transitionDelay: `${150 * index}ms` }}
                        >
                            <CardContent className="p-6">
                                <Quote className="h-8 w-8 text-steadi-pink mb-4 opacity-50" />
                                <p className="mb-6 text-lg">{testimonial.content}</p>
                                <div className="flex items-center">
                                    <Avatar className="h-10 w-10 mr-4">
                                        <AvatarImage src={testimonial.author.avatar || "/placeholder.svg"} alt={testimonial.author.name} />
                                        <AvatarFallback>{testimonial.author.name.charAt(0)}</AvatarFallback>
                                    </Avatar>
                                    <div>
                                        <p className="font-medium">{testimonial.author.name}</p>
                                        <p className="text-sm text-muted-foreground">
                                            {testimonial.author.role}, {testimonial.author.company}
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        </section>
    )
}
