"use client"

import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { toast } from "@/components/ui/use-toast"
import { ArrowLeft, Building2, Copy } from "lucide-react"

const orgFormSchema = z.object({
    orgCode: z.string().min(6, { message: "Organization code must be at least 6 characters" }),
})

type OrgFormValues = z.infer<typeof orgFormSchema>

export default function OrganizationPage() {
    const navigate = useNavigate()
    const [isSubmitting, setIsSubmitting] = useState(false)

    const form = useForm<OrgFormValues>({
        resolver: zodResolver(orgFormSchema),
        defaultValues: {
            orgCode: "",
        },
    })

    async function onSubmit(data: OrgFormValues) {
        setIsSubmitting(true)

        try {
            // Simulate API call
            await new Promise((resolve) => setTimeout(resolve, 1500))

            // Simulate validation
            if (data.orgCode !== "DEMO123") {
                form.setError("orgCode", {
                    type: "manual",
                    message: "Invalid organization code",
                })
                setIsSubmitting(false)
                return
            }

            toast({
                title: "Organization joined",
                description: "You have successfully joined the organization.",
            })

            navigate("/dashboard")
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to join organization. Please try again.",
                variant: "destructive",
            })
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <div className="flex min-h-screen w-full flex-col items-center justify-center bg-background p-4">
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute left-1/4 top-1/4 h-[500px] w-[500px] rounded-full bg-steadi-red/10 blur-[100px]" />
                <div className="absolute bottom-1/4 right-1/4 h-[600px] w-[600px] rounded-full bg-steadi-purple/10 blur-[100px]" />
                <div className="absolute left-1/2 top-1/2 h-[300px] w-[300px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-steadi-pink/10 blur-[100px]" />
                <div className="absolute inset-0 grid-pattern opacity-20" />
            </div>

            <div className="z-10 w-full max-w-md">
                <div className="flex flex-col items-center space-y-2 text-center">
                    <div className="flex items-center justify-center space-x-2">
                        <div className="relative flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-steadi-red via-steadi-pink to-steadi-purple p-[1px]">
                            <div className="flex h-full w-full items-center justify-center rounded-full bg-black">
                                <Building2 className="h-6 w-6 text-white" />
                            </div>
                        </div>
                        <span className="text-3xl font-bold steadi-gradient-text">Steadi.</span>
                    </div>
                    <h1 className="text-2xl font-bold tracking-tight">Join Organization</h1>
                    <p className="text-sm text-muted-foreground">Enter your organization code to join an existing workspace</p>
                </div>

                <Card className="mt-8 overflow-hidden border-0 bg-black/40 backdrop-blur-xl">
                    <CardHeader>
                        <CardTitle>Organization Access</CardTitle>
                        <CardDescription>Enter the code provided by your organization owner or manager</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Form {...form}>
                            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                                <FormField
                                    control={form.control}
                                    name="orgCode"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Organization Code</FormLabel>
                                            <FormControl>
                                                <div className="relative">
                                                    <Input
                                                        placeholder="Enter organization code"
                                                        {...field}
                                                        className="bg-muted/50 border-[#2a2a30] pr-10 font-mono"
                                                    />
                                                    <Button
                                                        type="button"
                                                        variant="ghost"
                                                        size="icon"
                                                        className="absolute right-0 top-0 h-full px-3 py-2 text-muted-foreground"
                                                        onClick={() => {
                                                            navigator.clipboard.writeText(field.value)
                                                            toast({
                                                                title: "Copied to clipboard",
                                                                description: "Organization code copied to clipboard",
                                                            })
                                                        }}
                                                    >
                                                        <Copy className="h-4 w-4" />
                                                        <span className="sr-only">Copy code</span>
                                                    </Button>
                                                </div>
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />

                                <div className="rounded-md bg-muted/30 p-3 text-sm">
                                    <p className="font-medium text-steadi-pink">Demo Code: DEMO123</p>
                                    <p className="mt-1 text-xs text-muted-foreground">Use this code for testing purposes</p>
                                </div>

                                <div className="flex justify-between">
                                    <Button
                                        type="button"
                                        variant="outline"
                                        onClick={() => navigate("/auth")}
                                        className="border-[#2a2a30] bg-transparent"
                                    >
                                        <ArrowLeft className="mr-2 h-4 w-4" />
                                        Back
                                    </Button>

                                    <Button
                                        type="submit"
                                        className="bg-gradient-to-r from-steadi-red via-steadi-pink to-steadi-purple hover:opacity-90"
                                        disabled={isSubmitting}
                                    >
                                        {isSubmitting ? "Joining..." : "Join Organization"}
                                    </Button>
                                </div>
                            </form>
                        </Form>
                    </CardContent>
                    <CardFooter className="flex justify-center border-t border-[#2a2a30] bg-muted/10 px-6 py-4">
                        <p className="text-xs text-muted-foreground">Don't have a code? Contact your organization administrator</p>
                    </CardFooter>
                </Card>
            </div>
        </div>
    )
}
