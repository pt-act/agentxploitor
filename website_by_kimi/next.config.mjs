/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  distDir: 'dist',
  images: {
    unoptimized: true,
  },
  // Fix turbopack root inference in monorepo (multiple lockfiles detected)
  turbo: {
    root: '..',
  },
}

export default nextConfig
