import { Sparkles } from "lucide-react"

export function AuthHeader() {
    return (
        <div className="flex flex-col items-center space-y-2 text-center">
            <div className="flex items-center justify-center space-x-2">
                <div className="relative flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-steadi-red via-steadi-pink to-steadi-purple p-[1px]">
                    <div className="flex h-full w-full items-center justify-center rounded-full bg-black">
                        <Sparkles className="h-6 w-6 text-white" />
                    </div>
                </div>
                <span className="text-3xl font-bold steadi-gradient-text">Steadi.</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Welcome to Steadi</h1>
            <p className="text-sm text-muted-foreground">Sign in to your account or create a new one to get started</p>
        </div>
    )
}
