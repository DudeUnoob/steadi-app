import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"

export function LandingFooter() {
    const currentYear = new Date().getFullYear()

    return (
        <footer className="border-t border-[#2a2a30] bg-black/40 py-12">
            <div className="container px-4 md:px-6">
                <Link to="/" className="flex items-center space-x-2 mb-4">
                    <div className="flex items-center">
                        <div className="h-8 w-8 bg-gradient-to-r from-steadi-red to-steadi-purple rounded-md"></div>
                        <span className="ml-2 text-2xl font-semibold">Steadi.</span>
                    </div>
                </Link>

                <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-6 gap-8 py-6">
                    <div className="md:col-span-2">
                        <h3 className="text-lg font-semibold mb-4">About Steadi</h3>
                        <p className="text-muted-foreground mb-4 max-w-sm">
                            Steadi is an AI-powered platform for small businesses to optimize their
                            supply chain management and customer acquisition with advanced technology.
                        </p>
                        <div className="flex space-x-4">
                            <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                                    <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"></path>
                                </svg>
                                <span className="sr-only">Twitter</span>
                            </Button>
                        </div>
                    </div>

                    <div>
                        <h3 className="text-base font-semibold mb-4">Product</h3>
                        <ul className="space-y-3">
                            <li>
                                <a href="#features" className="text-muted-foreground hover:text-foreground">
                                    Features
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground">
                                    Pricing
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground">
                                    Integrations
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground">
                                    Changelog
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground">
                                    Documentation
                                </a>
                            </li>
                        </ul>
                    </div>

                    <div>
                        <h3 className="text-base font-semibold mb-4">Company</h3>
                        <ul className="space-y-3">
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground">
                                    About
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground">
                                    Blog
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground">
                                    Careers
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground">
                                    Customers
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground">
                                    Partners
                                </a>
                            </li>
                        </ul>
                    </div>

                    <div>
                        <h3 className="text-base font-semibold mb-4">Resources</h3>
                        <ul className="space-y-3">
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground">
                                    Support
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground">
                                    Contact
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground">
                                    Privacy
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>

                <div className="flex flex-col md:flex-row justify-between items-center border-t border-[#2a2a30] pt-8 mt-8">
                    <p className="text-sm text-muted-foreground">© {currentYear} Steadi, Inc. All rights reserved.</p>
                    <div className="flex space-x-4 mt-4 md:mt-0">
                        <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                            Terms of Service
                        </a>
                        <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                            Privacy Policy
                        </a>
                        <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                            Cookies
                        </a>
                    </div>
                </div>
            </div>
        </footer>
    )
}
