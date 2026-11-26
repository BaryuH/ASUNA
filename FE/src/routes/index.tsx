import { createFileRoute } from '@tanstack/react-router'
import Workstation from '../components/Workstation'

export const Route = createFileRoute('/')({
  component: Workstation,
})
