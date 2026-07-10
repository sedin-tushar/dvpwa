require "rails_helper"

RSpec.describe "Error pages", type: :request do
  describe "GET unknown path" do
    it "returns 404" do
      get "/this-path-does-not-exist"
      expect(response).to have_http_status(:not_found)
    end
  end
end
