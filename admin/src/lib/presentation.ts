const labels: Record<string, string> = {
  admin: 'Administrador',
  curator: 'Curador',
  reviewer: 'Revisor',
  student: 'Estudante',
  needs_review: 'Precisa de revisão',
  approved: 'Aprovado',
  published: 'Publicado',
  reported: 'Reportado',
  revised: 'Revisado',
  deprecated: 'Depreciado',
  archived: 'Arquivado',
  rejected: 'Rejeitado',
  superseded: 'Substituído',
  draft: 'Rascunho',
  open: 'Aberto',
  in_review: 'Em revisão',
  resolved: 'Resolvido',
  pending: 'Pendente',
  assigned: 'Atribuído',
  completed: 'Concluído',
  cancelled: 'Cancelado',
  active: 'Ativo',
  inactive: 'Inativo',
  subscribed: 'Assinado',
  added: 'Adicionado',
  updated: 'Atualizado',
  removed: 'Removido',
  ready: 'Valido',
  created: 'Criado',
  duplicate: 'Duplicado',
  error: 'Erro',
  converted_to_new_version: 'Convertido em nova versão',
  wrong_answer: 'Resposta incorreta',
  bad_explanation: 'Explicação inadequada',
  outdated_law: 'Legislação desatualizada',
  classification_error: 'Erro de classificação',
  duplicate_card: 'Cartão duplicado',
  typo: 'Erro de digitação',
  suggestion: 'Sugestão',
}

export function translateStatus(value: string) {
  return labels[value] ?? value.replaceAll('_', ' ')
}

export function formatDate(value: string | null) {
  if (!value) return 'Nunca'
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value))
}
