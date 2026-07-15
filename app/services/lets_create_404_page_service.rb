# Approve (3 files selected)
class LetsCreate404PageService
  def initialize(params = {})
    @params = params
  end

  def call
    perform
  end

  private

  def perform
    raise NotImplementedError, "Implement this service"
  end
end
