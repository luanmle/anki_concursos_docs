type ExploreHeroProps = {
  eyebrow: string
  title: string
  description: string
}

export function ExploreHero({ eyebrow, title, description }: ExploreHeroProps) {
  return (
    <header className="muriae-explore-hero">
      <span className="muriae-eyebrow">{eyebrow}</span>
      <h1 className="muriae-display">{title}</h1>
      <p className="muriae-lede">{description}</p>
    </header>
  )
}
