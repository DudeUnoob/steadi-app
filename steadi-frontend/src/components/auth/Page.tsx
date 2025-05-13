"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card } from "@/components/ui/card"
import { SignupForm } from "./SignupForm"
import { LoginForm } from "./LoginForm"
import { AuthHeader } from "./AuthHeader"

export function NewAuthPage() {
    const [activeTab, setActiveTab] = useState<string>("signup")

    return (
        <div className="flex min-h-screen w-full flex-col items-center justify-center bg-background p-4">
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute left-1/4 top-1/4 h-[500px] w-[500px] rounded-full bg-steadi-red/10 blur-[100px]" />
                <div className="absolute bottom-1/4 right-1/4 h-[600px] w-[600px] rounded-full bg-steadi-purple/10 blur-[100px]" />
                <div className="absolute left-1/2 top-1/2 h-[300px] w-[300px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-steadi-pink/10 blur-[100px]" />
                <div className="absolute inset-0 grid-pattern opacity-20" />
            </div>

            <div className="z-10 w-full max-w-md">
                <AuthHeader />

                <Card className="mt-8 overflow-hidden border-0 bg-black/40 backdrop-blur-xl">
                    <div className="p-6">
                        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                            <TabsList className="grid w-full grid-cols-2">
                                <TabsTrigger value="signup">Sign Up</TabsTrigger>
                                <TabsTrigger value="login">Login</TabsTrigger>
                            </TabsList>
                            <TabsContent value="signup" className="mt-6">
                                <SignupForm />
                            </TabsContent>
                            <TabsContent value="login" className="mt-6">
                                <LoginForm />
                            </TabsContent>
                        </Tabs>
                    </div>
                </Card>
            </div>
        </div>
    )
}
