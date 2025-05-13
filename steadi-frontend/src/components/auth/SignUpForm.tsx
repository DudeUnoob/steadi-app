"use client"

import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/components/ui/use-toast"
import { Eye, EyeOff } from "lucide-react"
import { useAuth } from "@/lib/AuthContext"

const signupFormSchema = z.object({
    username: z
        .string()
        .min(3, { message: "Username must be at least 3 characters" })
        .max(50, { message: "Username must not exceed 50 characters" }),
    email: z.string().email({ message: "Please enter a valid email address" }),
    password: z
        .string()
        .min(8, { message: "Password must be at least 8 characters" })
        .regex(/[A-Z]/, { message: "Password must contain at least one uppercase letter" })
        .regex(/[a-z]/, { message: "Password must contain at least one lowercase letter" })
        .regex(/[0-9]/, { message: "Password must contain at least one number" }),
    role: z.enum(["owner", "manager", "staff"], {
        required_error: "Please select a role",
    }),
    orgCode: z.string().optional(),
})

type SignupFormValues = z.infer<typeof signupFormSchema>

export function SignupForm() {
    const navigate = useNavigate()
    const { toast } = useToast()
    const { signUp } = useAuth()
    const [showPassword, setShowPassword] = useState(false)
    const [isSubmitting, setIsSubmitting] = useState(false)

    const form = useForm<SignupFormValues>({
        resolver: zodResolver(signupFormSchema),
        defaultValues: {
            username: "",
            email: "",
            password: "",
            role: "staff",
            orgCode: "",
        },
    })

    const selectedRole = form.watch("role")

    async function onSubmit(data: SignupFormValues) {
        setIsSubmitting(true)

        try {
            // Organization code validation for non-owners
            if (data.role !== "owner" && (!data.orgCode || data.orgCode.trim() === "")) {
                form.setError("orgCode", {
                    type: "manual",
                    message: "Organization code is required for non-owner roles",
                })
                setIsSubmitting(false)
                return
            }

            // Register the user with Supabase
            const response = await signUp(data.email, data.password)

            if (response.error) {
                throw new Error(response.error.message || "Failed to create account")
            }

            if (response.needsEmailVerification) {
                toast({
                    title: "Verification email sent",
                    description: "Please check your email to verify your account.",
                })
                navigate("/auth") // Return to auth page
                return
            }

            toast({
                title: "Account created successfully",
                description: `Welcome, ${data.username}!`,
            })

            navigate("/dashboard")
        } catch (error: any) {
            toast({
                title: "Error",
                description: error.message || "Something went wrong. Please try again.",
                variant: "destructive",
            })
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                <FormField
                    control={form.control}
                    name="username"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Username</FormLabel>
                            <FormControl>
                                <Input placeholder="Enter your username" {...field} className="bg-muted/50 border-[#2a2a30]" />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />

                <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Email</FormLabel>
                            <FormControl>
                                <Input
                                    type="email"
                                    placeholder="Enter your email"
                                    {...field}
                                    className="bg-muted/50 border-[#2a2a30]"
                                />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />

                <FormField
                    control={form.control}
                    name="password"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Password</FormLabel>
                            <FormControl>
                                <div className="relative">
                                    <Input
                                        type={showPassword ? "text" : "password"}
                                        placeholder="Create a password"
                                        {...field}
                                        className="bg-muted/50 border-[#2a2a30] pr-10"
                                    />
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        className="absolute right-0 top-0 h-full px-3 py-2 text-muted-foreground"
                                        onClick={() => setShowPassword(!showPassword)}
                                    >
                                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                        <span className="sr-only">{showPassword ? "Hide password" : "Show password"}</span>
                                    </Button>
                                </div>
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />

                <FormField
                    control={form.control}
                    name="role"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Role</FormLabel>
                            <Select onValueChange={field.onChange} defaultValue={field.value}>
                                <FormControl>
                                    <SelectTrigger className="bg-muted/50 border-[#2a2a30]">
                                        <SelectValue placeholder="Select your role" />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    <SelectItem value="owner">Owner</SelectItem>
                                    <SelectItem value="manager">Manager</SelectItem>
                                    <SelectItem value="staff">Staff</SelectItem>
                                </SelectContent>
                            </Select>
                            <FormMessage />
                        </FormItem>
                    )}
                />

                {selectedRole !== "owner" && (
                    <FormField
                        control={form.control}
                        name="orgCode"
                        render={({ field }) => (
                            <FormItem>
                                <FormLabel>Organization Code</FormLabel>
                                <FormControl>
                                    <Input placeholder="Enter organization code" {...field} className="bg-muted/50 border-[#2a2a30]" />
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                        )}
                    />
                )}

                <Button type="submit" className="w-full bg-steadi-pink hover:bg-steadi-pink/90" disabled={isSubmitting}>
                    {isSubmitting ? "Creating Account..." : "Create Account"}
                </Button>
            </form>
        </Form>
    )
}
